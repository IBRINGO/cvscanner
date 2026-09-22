"""Django ORM-backed implementation of the DocumentRepository contract
application/documents use cases depend on (duck-typed - see e.g.
application/documents/upload_document.py's docstring). Converts every
Django Document row to/from domain.documents.entities.DocumentRecord so
application code never touches a Django model instance directly.
"""
from apps.documents.models import Document as DjangoDocument
from domain.documents.entities import DocumentRecord
from domain.documents.enums import DocumentType, ProcessingStatus


def _to_record(row: DjangoDocument) -> DocumentRecord:
    return DocumentRecord(
        id=str(row.id),
        owner_id=str(row.owner_id) if row.owner_id else None,
        document_type=DocumentType(row.document_type),
        original_filename=row.original_filename,
        mime_type=row.mime_type,
        file_size=row.file_size,
        file_hash=row.file_hash,
        status=ProcessingStatus(row.status),
        page_count=row.page_count,
        processing_metadata=row.processing_metadata,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class DjangoDocumentRepository:
    def create(
        self,
        *,
        document_type: DocumentType,
        original_filename: str,
        mime_type: str,
        file_size: int,
        file_hash: str,
        storage_reference: str,
        owner_id: str | None = None,
    ) -> DocumentRecord:
        row = DjangoDocument.objects.create(
            document_type=document_type.value,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            file_hash=file_hash,
            storage_reference=storage_reference,
            owner_id=owner_id,
        )
        return _to_record(row)

    def get(self, document_id: str) -> DocumentRecord:
        return _to_record(DjangoDocument.objects.get(id=document_id))

    def find_by_hash(
        self, *, file_hash: str, document_type: DocumentType, owner_id: str | None = None
    ) -> DocumentRecord | None:
        row = DjangoDocument.objects.filter(
            file_hash=file_hash, document_type=document_type.value, owner_id=owner_id
        ).first()
        return _to_record(row) if row else None

    def get_storage_reference(self, document_id: str) -> str:
        return DjangoDocument.objects.values_list("storage_reference", flat=True).get(id=document_id)

    def update_status(self, document_id: str, status: ProcessingStatus) -> None:
        DjangoDocument.objects.filter(id=document_id).update(status=status.value)

    def save_parsed_result(
        self, document_id: str, *, raw_text: str, page_count: int | None, sections: list[dict]
    ) -> None:
        DjangoDocument.objects.filter(id=document_id).update(
            extracted_text=raw_text, page_count=page_count, sections=sections
        )

    def update_processing_metadata(self, document_id: str, **fields) -> None:
        row = DjangoDocument.objects.get(id=document_id)
        row.processing_metadata = {**row.processing_metadata, **fields}
        row.save(update_fields=["processing_metadata"])

    def mark_failed(self, document_id: str, error_message: str) -> None:
        row = DjangoDocument.objects.get(id=document_id)
        row.status = ProcessingStatus.FAILED.value
        row.processing_metadata = {**row.processing_metadata, "error": error_message}
        row.save(update_fields=["status", "processing_metadata"])

    def list_documents(self, document_type: DocumentType) -> list[DocumentRecord]:
        return [_to_record(row) for row in DjangoDocument.objects.filter(document_type=document_type.value)]
