"""Evidence: the provenance record attached to an extracted fact.

Every skill, experience entry, education entry, certification, and job
requirement that Phase 2 extracts is backed by one of these. This is what
lets a later phase say "the system claims this candidate knows Python
because of this exact sentence, on this exact page" instead of asserting
facts out of nowhere.

IMPORTANT - what `confidence` means (and does not mean):

    confidence is a measure of EXTRACTION confidence: how sure the
    extraction method is that it read the source text correctly and
    classified it correctly. It is NOT a probability that the underlying
    claim is true. A confidence of 0.98 on the skill "Python" means "the
    parser is 98% sure this token appeared verbatim in a Skills section
    and was matched to the Python skill in the taxonomy" - it says
    nothing about whether the candidate is actually proficient in Python.
    Do not let later phases (matching, scoring) reinterpret this number
    as a truth probability.
"""
from dataclasses import dataclass, field

from domain.documents.enums import ExtractionMethod, SectionType


@dataclass(frozen=True)
class Evidence:
    source_document_id: str
    text: str
    extraction_method: ExtractionMethod
    confidence: float
    page_number: int | None = None
    section: SectionType | None = None
    start_offset: int | None = None
    end_offset: int | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")
