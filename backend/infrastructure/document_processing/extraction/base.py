"""Structured-extraction abstraction (section 26 of the Phase 2 brief).

`CandidateExtractor` and `JobExtractor` are the "StructuredExtractor"
concept the brief asks for, split into two concrete Protocols rather than
one generic one (simpler, and Phase 2 never needs to treat them
polymorphically). `RuleBasedCandidateExtractor`/`RuleBasedJobExtractor`
(this package) are the only implementations today; a future
`LLMStructuredExtractor` would implement the same Protocol and could be
swapped in via config/container.py without touching application code.
"""
from typing import Protocol

from domain.cv.entities import CandidateProfile
from domain.documents.entities import DetectedSection, ParsedDocument
from domain.documents.evidence import Evidence
from domain.job.entities import JobProfile


class CandidateExtractor(Protocol):
    def extract(
        self, *, document_id: str, parsed: ParsedDocument, sections: list[DetectedSection]
    ) -> tuple[CandidateProfile, list[Evidence]]: ...


class JobExtractor(Protocol):
    def extract(
        self, *, document_id: str, parsed: ParsedDocument, sections: list[DetectedSection]
    ) -> tuple[JobProfile, list[Evidence]]: ...
