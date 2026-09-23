"""Analysis creation use case (Phase 4 section 4/34).

Deliberately does not upload or process documents - it only accepts
references to CVs/job offers Phase 2 has already ingested (section 34:
"do not upload documents again from the analysis endpoint"). Creates a
PENDING row and returns immediately; the actual matching pipeline runs
asynchronously - see application/matching/run_analysis.py.

    document_repository needs: get(document_id) -> DocumentRecord
    analysis_repository needs: create_pending(candidate_id, job_id, engine_version) -> str
"""
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.matching.exceptions import AnalysisValidationError


class CreateAnalysis:
    def __init__(self, document_repository, analysis_repository, engine_version: str) -> None:
        self._document_repository = document_repository
        self._analysis_repository = analysis_repository
        self._engine_version = engine_version

    def execute(self, candidate_document_id: str, job_document_id: str) -> str:
        candidate_document = self._document_repository.get(candidate_document_id)
        job_document = self._document_repository.get(job_document_id)

        if candidate_document.document_type != DocumentType.CV:
            raise AnalysisValidationError("candidate_document_id must reference a CV.")
        if job_document.document_type != DocumentType.JOB_OFFER:
            raise AnalysisValidationError("job_document_id must reference a job offer.")
        if candidate_document.status != ProcessingStatus.PROCESSED:
            raise AnalysisValidationError("The CV has not finished processing yet.")
        if job_document.status != ProcessingStatus.PROCESSED:
            raise AnalysisValidationError("The job offer has not finished processing yet.")

        return self._analysis_repository.create_pending(
            candidate_document_id, job_document_id, self._engine_version
        )
