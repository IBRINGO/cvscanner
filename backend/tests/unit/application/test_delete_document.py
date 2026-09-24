"""Tests DeleteDocument against fake repository/storage/semantic-repository
doubles - no Django, no database. See application/documents/delete_document.py.
"""
import pytest

from application.documents.delete_document import DeleteDocument
from domain.documents.entities import DocumentRecord
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.semantics.enums import SemanticEntityType


class FakeDocumentRepository:
    def __init__(self, record: DocumentRecord, storage_reference: str) -> None:
        self._record = record
        self._storage_reference = storage_reference
        self.deleted_ids: list[str] = []

    def get(self, document_id):
        return self._record

    def get_storage_reference(self, document_id):
        return self._storage_reference

    def delete(self, document_id):
        self.deleted_ids.append(document_id)


class FakeFileStorage:
    def __init__(self) -> None:
        self.deleted_references: list[str] = []

    def delete(self, reference):
        self.deleted_references.append(reference)


class FakeSemanticRepresentationRepository:
    def __init__(self) -> None:
        self.deleted: list[tuple[SemanticEntityType, str]] = []

    def delete_for_entity(self, entity_type, entity_id):
        self.deleted.append((entity_type, entity_id))


def _document_record(document_type: DocumentType) -> DocumentRecord:
    return DocumentRecord(
        id="doc-1",
        owner_id=None,
        document_type=document_type,
        original_filename="cv.pdf",
        mime_type="application/pdf",
        file_size=100,
        file_hash="a" * 64,
        status=ProcessingStatus.PROCESSED,
        page_count=1,
        processing_metadata={},
        created_at=None,
        updated_at=None,
    )


class TestDeleteDocument:
    def test_deletes_the_document_row(self):
        repository = FakeDocumentRepository(_document_record(DocumentType.CV), "cv/abc.pdf")
        use_case = DeleteDocument(repository, FakeFileStorage(), FakeSemanticRepresentationRepository())

        use_case.execute("doc-1")

        assert repository.deleted_ids == ["doc-1"]

    def test_deletes_the_stored_file(self):
        repository = FakeDocumentRepository(_document_record(DocumentType.CV), "cv/abc.pdf")
        storage = FakeFileStorage()
        use_case = DeleteDocument(repository, storage, FakeSemanticRepresentationRepository())

        use_case.execute("doc-1")

        assert storage.deleted_references == ["cv/abc.pdf"]

    def test_sweeps_candidate_profile_embeddings_for_a_cv(self):
        repository = FakeDocumentRepository(_document_record(DocumentType.CV), "cv/abc.pdf")
        semantic_repository = FakeSemanticRepresentationRepository()
        use_case = DeleteDocument(repository, FakeFileStorage(), semantic_repository)

        use_case.execute("doc-1")

        assert semantic_repository.deleted == [(SemanticEntityType.CANDIDATE_PROFILE, "doc-1")]

    def test_sweeps_job_profile_embeddings_for_a_job_offer(self):
        repository = FakeDocumentRepository(_document_record(DocumentType.JOB_OFFER), "job_offer/abc.pdf")
        semantic_repository = FakeSemanticRepresentationRepository()
        use_case = DeleteDocument(repository, FakeFileStorage(), semantic_repository)

        use_case.execute("doc-1")

        assert semantic_repository.deleted == [(SemanticEntityType.JOB_PROFILE, "doc-1")]


@pytest.mark.parametrize("document_type", [DocumentType.CV, DocumentType.JOB_OFFER])
def test_works_for_both_document_types(document_type):
    repository = FakeDocumentRepository(_document_record(document_type), "ref")
    use_case = DeleteDocument(repository, FakeFileStorage(), FakeSemanticRepresentationRepository())

    use_case.execute("doc-1")

    assert repository.deleted_ids == ["doc-1"]
