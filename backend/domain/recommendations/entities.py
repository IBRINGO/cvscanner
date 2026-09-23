"""The Recommendation domain model (Phase 5 sections 6-13).

Deliberately thin: a Recommendation never carries its own copy of
evidence text or requirement details beyond what it needs to explain
itself (section 10) - `related_requirement_index` points back at the
originating `RequirementEvaluation`'s position within the analysis
(the same positional identity the frontend's requirement matrix
already uses), and `supporting_evidence` reuses
`domain.matching.entities.MatchEvidence` directly rather than
duplicating its shape.
"""
from dataclasses import dataclass, field

from domain.matching.entities import MatchEvidence
from domain.recommendations.enums import (
    RecommendationConfidence,
    RecommendationImpact,
    RecommendationPriority,
    RecommendationSafety,
    RecommendationType,
)


@dataclass(frozen=True)
class Recommendation:
    type: RecommendationType
    priority: RecommendationPriority
    confidence: RecommendationConfidence
    safety: RecommendationSafety
    impact: RecommendationImpact
    title: str
    summary: str
    reason: str
    suggested_action: str
    related_requirement_index: int | None = None
    supporting_evidence: tuple[MatchEvidence, ...] = field(default_factory=tuple)
    current_state: str | None = None
    target_state: str | None = None

    @property
    def safe_to_tailor(self) -> bool:
        """A recommendation can feed an automatic TailoringPlan only when
        it is SAFE_TO_REPHRASE or SAFE_TO_REORDER (section 11).
        REQUIRES_CANDIDATE_CONFIRMATION and NOT_SAFE_TO_AUTOMATE are
        informational only - the candidate acts on them manually.
        """
        return self.safety in (
            RecommendationSafety.SAFE_TO_REPHRASE,
            RecommendationSafety.SAFE_TO_REORDER,
        )
