"""Upload use case (sections 8-9, 25, 36, 75 of the Phase 2 brief).

Dependencies are duck-typed constructor parameters, not imported
Protocols - see docs/architecture/dependency-rule.md's "composition root"
note. This keeps application/ importing nothing but domain/ and stdlib.

    repository needs: create(...) -> DocumentRecord,
                       find_by_hash(...) -> DocumentRecord | None
    storage needs:    save(content: bytes, key: str) -> str

Duplicate uploads (section 75): the same file (by sha256 hash), for the
same document_type and owner, reuses the existing Document instead of
creating a new one or rejecting the upload. This is a deliberate choice -
see docs/architecture/phase-2-pipeline.md "Duplicate upload handling" -
made so re-uploading (e.g. after a network hiccup) never creates
duplicate processing work or duplicate rows.
"""
import hashlib
from dataclasses import dataclass

from domain.documents.entities import DocumentRecord
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.documents.policies import SUPPORTED_MIME_TYPES, validate_file


@dataclass(frozen=True)
class UploadResult:
    document: DocumentRecord
    is_new: bool

    @property
    def needs_processing(self) -> bool:
        """Whether the caller should enqueue processing. False when the
        document was already PROCESSED, or is already VALIDATING/
        PROCESSING (avoids duplicate concurrent processing runs).
        """
        return self.document.status in (ProcessingStatus.UPLOADED, ProcessingStatus.FAILED)


class UploadDocument:
    def __init__(self, repository, storage) -> None:
        self._repository = repository
        self._storage = storage

    def execute(
        self,
        *,
        document_type: DocumentType,
        content: bytes,
        original_filename: str,
        mime_type: str,
        owner_id: str | None = None,
    ) -> UploadResult:
        validate_file(filename=original_filename, mime_type=mime_type, size_bytes=len(content))

        file_hash = hashlib.sha256(content).hexdigest()
        existing = self._repository.find_by_hash(
            file_hash=file_hash, document_type=document_type, owner_id=owner_id
        )
        if existing is not None:
            return UploadResult(document=existing, is_new=False)

        extension = SUPPORTED_MIME_TYPES[mime_type]
        storage_key = f"{document_type.value.lower()}/{file_hash}{extension}"
        storage_reference = self._storage.save(content, storage_key)

        document = self._repository.create(
            document_type=document_type,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=len(content),
            file_hash=file_hash,
            storage_reference=storage_reference,
            owner_id=owner_id,
        )
        return UploadResult(document=document, is_new=True)
