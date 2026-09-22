"""Tests UploadDocument against fake repository/storage doubles - no
Django, no database. See application/documents/upload_document.py.
"""
import dataclasses

import pytest

from application.documents.upload_document import UploadDocument
from domain.documents.entities import DocumentRecord
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.documents.exceptions import DocumentValidationError


class FakeDocumentRepository:
    def __init__(self):
        self.created = []

    def find_by_hash(self, *, file_hash, document_type, owner_id=None):
        for record in self.created:
            if record.file_hash == file_hash and record.document_type == document_type:
                return record
        return None

    def create(
        self,
        *,
        document_type,
        original_filename,
        mime_type,
        file_size,
        file_hash,
        storage_reference,
        owner_id=None,
    ):
        record = DocumentRecord(
            id=f"doc-{len(self.created) + 1}",
            owner_id=owner_id,
            document_type=document_type,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            file_hash=file_hash,
            status=ProcessingStatus.UPLOADED,
            page_count=None,
            processing_metadata={},
            created_at=None,
            updated_at=None,
        )
        self.created.append(record)
        return record


class FakeFileStorage:
    def __init__(self):
        self.saved = {}

    def save(self, content, key):
        self.saved[key] = content
        return key


@pytest.fixture
def repository():
    return FakeDocumentRepository()


@pytest.fixture
def storage():
    return FakeFileStorage()


class TestUploadDocument:
    def test_uploads_a_valid_pdf(self, repository, storage):
        use_case = UploadDocument(repository, storage)

        result = use_case.execute(
            document_type=DocumentType.CV,
            content=b"%PDF-1.4 fake content",
            original_filename="cv.pdf",
            mime_type="application/pdf",
        )

        assert result.is_new is True
        assert result.needs_processing is True
        assert len(storage.saved) == 1

    def test_rejects_invalid_file(self, repository, storage):
        use_case = UploadDocument(repository, storage)

        with pytest.raises(DocumentValidationError):
            use_case.execute(
                document_type=DocumentType.CV,
                content=b"",
                original_filename="cv.pdf",
                mime_type="application/pdf",
            )

    def test_duplicate_upload_reuses_existing_document(self, repository, storage):
        use_case = UploadDocument(repository, storage)
        content = b"%PDF-1.4 identical content"

        first = use_case.execute(
            document_type=DocumentType.CV,
            content=content,
            original_filename="cv.pdf",
            mime_type="application/pdf",
        )
        second = use_case.execute(
            document_type=DocumentType.CV,
            content=content,
            original_filename="cv-again.pdf",
            mime_type="application/pdf",
        )

        assert first.document.id == second.document.id
        assert second.is_new is False
        assert len(repository.created) == 1
        assert len(storage.saved) == 1  # file was not re-saved

    def test_different_document_type_is_not_treated_as_duplicate(self, repository, storage):
        use_case = UploadDocument(repository, storage)
        content = b"%PDF-1.4 shared bytes"

        cv_result = use_case.execute(
            document_type=DocumentType.CV,
            content=content,
            original_filename="cv.pdf",
            mime_type="application/pdf",
        )
        job_result = use_case.execute(
            document_type=DocumentType.JOB_OFFER,
            content=content,
            original_filename="job.pdf",
            mime_type="application/pdf",
        )

        assert cv_result.document.id != job_result.document.id

    def test_needs_processing_is_false_once_processed(self, repository, storage):
        use_case = UploadDocument(repository, storage)
        content = b"%PDF-1.4 already processed"

        use_case.execute(
            document_type=DocumentType.CV,
            content=content,
            original_filename="cv.pdf",
            mime_type="application/pdf",
        )
        repository.created[0] = dataclasses.replace(
            repository.created[0], status=ProcessingStatus.PROCESSED
        )

        reused = use_case.execute(
            document_type=DocumentType.CV,
            content=content,
            original_filename="cv.pdf",
            mime_type="application/pdf",
        )
        assert reused.needs_processing is False
