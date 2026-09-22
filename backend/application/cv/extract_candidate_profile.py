"""Extraction use case (sections 14-19 of the Phase 2 brief).

    extractor needs:  extract(document_id=, parsed=, sections=)
                       -> tuple[CandidateProfile, list[Evidence]]
    repository needs: save(document_id, profile, document_level_evidence) -> None

See infrastructure/document_processing/extraction/candidate_extractor.py
for the concrete rule-based implementation this is built to swap out
later (an LLM-assisted extractor would implement the same shape).
"""
from domain.cv.entities import CandidateProfile
from domain.documents.entities import DetectedSection, ParsedDocument


class ExtractCandidateProfile:
    def __init__(self, extractor, repository) -> None:
        self._extractor = extractor
        self._repository = repository

    def execute(
        self, document_id: str, parsed: ParsedDocument, sections: list[DetectedSection]
    ) -> CandidateProfile:
        profile, document_level_evidence = self._extractor.extract(
            document_id=document_id, parsed=parsed, sections=sections
        )
        self._repository.save(document_id, profile, document_level_evidence)
        return profile
