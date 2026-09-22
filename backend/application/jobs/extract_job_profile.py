"""Extraction use case (sections 21-23 of the Phase 2 brief). See
application/cv/extract_candidate_profile.py - same shape, job-specific
domain type.
"""
from domain.documents.entities import DetectedSection, ParsedDocument
from domain.job.entities import JobProfile


class ExtractJobProfile:
    def __init__(self, extractor, repository) -> None:
        self._extractor = extractor
        self._repository = repository

    def execute(
        self, document_id: str, parsed: ParsedDocument, sections: list[DetectedSection]
    ) -> JobProfile:
        profile, document_level_evidence = self._extractor.extract(
            document_id=document_id, parsed=parsed, sections=sections
        )
        self._repository.save(document_id, profile, document_level_evidence)
        return profile
