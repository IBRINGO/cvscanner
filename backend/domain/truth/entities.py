"""The Truth Layer's data model (Phase 5 sections 14-17).

A `CandidateFact` is a read-only, structured view over one piece of
`CandidateProfile` that generated content is allowed to draw from. It
never duplicates `CandidateProfile`/`Evidence` data beyond what the
Truth Layer needs to reason about a fact independently: what it is,
how sure we are of it, and what may safely happen to its wording.
"""
from dataclasses import dataclass, field

from domain.documents.evidence import Evidence
from domain.truth.enums import AllowedTransformation, FactType, VerificationStatus


@dataclass(frozen=True)
class CandidateFact:
    id: str
    type: FactType
    value: str
    normalized_value: str | None
    confidence: float
    verification_status: VerificationStatus
    allowed_transformations: tuple[AllowedTransformation, ...] = field(default_factory=tuple)
    evidence: Evidence | None = None

    def permits(self, transformation: AllowedTransformation) -> bool:
        return transformation in self.allowed_transformations
