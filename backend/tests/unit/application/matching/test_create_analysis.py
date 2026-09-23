import pytest

from application.matching.create_analysis import CreateAnalysis
from domain.documents.entities import DocumentRecord
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.matching.exceptions import AnalysisValidationError


def _document(document_type=DocumentType.CV, status=ProcessingStatus.PROCESSED) -> DocumentRecord:
    return DocumentRecord(
        id="doc-1", owner_id=None, document_type=document_type, original_filename="f",
        mime_type="application/pdf", file_size=1, file_hash="x", status=status,
        page_count=None, processing_metadata={}, created_at=None, updated_at=None,
    )


class FakeDocumentRepository:
    def __init__(self, documents: dict):
        self._documents = documents

    def get(self, document_id):
        return self._documents[document_id]


class FakeAnalysisRepository:
    def __init__(self):
        self.created = None

    def create_pending(self, candidate_document_id, job_document_id, engine_version):
        self.created = (candidate_document_id, job_document_id, engine_version)
        return "analysis-1"


class TestCreateAnalysis:
    def test_creates_a_pending_analysis_for_two_processed_documents(self):
        documents = {
            "cv-1": _document(DocumentType.CV),
            "job-1": _document(DocumentType.JOB_OFFER),
        }
        analysis_repository = FakeAnalysisRepository()
        use_case = CreateAnalysis(FakeDocumentRepository(documents), analysis_repository, "1.0.0")

        analysis_id = use_case.execute("cv-1", "job-1")

        assert analysis_id == "analysis-1"
        assert analysis_repository.created == ("cv-1", "job-1", "1.0.0")

    def test_rejects_a_job_offer_as_the_candidate_document(self):
        documents = {"a": _document(DocumentType.JOB_OFFER), "b": _document(DocumentType.JOB_OFFER)}
        use_case = CreateAnalysis(FakeDocumentRepository(documents), FakeAnalysisRepository(), "1.0.0")

        with pytest.raises(AnalysisValidationError):
            use_case.execute("a", "b")

    def test_rejects_a_cv_as_the_job_document(self):
        documents = {"a": _document(DocumentType.CV), "b": _document(DocumentType.CV)}
        use_case = CreateAnalysis(FakeDocumentRepository(documents), FakeAnalysisRepository(), "1.0.0")

        with pytest.raises(AnalysisValidationError):
            use_case.execute("a", "b")

    def test_rejects_an_unprocessed_cv(self):
        documents = {
            "cv-1": _document(DocumentType.CV, ProcessingStatus.PROCESSING),
            "job-1": _document(DocumentType.JOB_OFFER),
        }
        use_case = CreateAnalysis(FakeDocumentRepository(documents), FakeAnalysisRepository(), "1.0.0")

        with pytest.raises(AnalysisValidationError):
            use_case.execute("cv-1", "job-1")

    def test_rejects_an_unprocessed_job_offer(self):
        documents = {
            "cv-1": _document(DocumentType.CV),
            "job-1": _document(DocumentType.JOB_OFFER, ProcessingStatus.FAILED),
        }
        use_case = CreateAnalysis(FakeDocumentRepository(documents), FakeAnalysisRepository(), "1.0.0")

        with pytest.raises(AnalysisValidationError):
            use_case.execute("cv-1", "job-1")
