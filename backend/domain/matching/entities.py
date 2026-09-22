"""The ATS Analysis domain model (section 25 of the Phase 4 brief).

Reuses `domain.documents.evidence.Evidence` directly rather than
duplicating its shape - a `MatchEvidence` only adds the matching-specific
context of *where in the candidate profile* that evidence came from
(section 9/10: evidence must be traceable and evidence hierarchy must be
explainable).
"""
from dataclasses import dataclass, field

from domain.documents.evidence import Evidence
from domain.job.enums import RequirementType
from domain.matching.enums import (
    AnalysisStatus,
    MatchSignal,
    MatchStrength,
    RequirementPriority,
    RequirementStatus,
)


@dataclass(frozen=True)
class MatchEvidence:
    evidence: Evidence
    source_type: str
    source_label: str | None = None


@dataclass(frozen=True)
class RequirementEvaluation:
    requirement_type: RequirementType
    priority: RequirementPriority
    raw_text: str
    status: RequirementStatus
    match_signal: MatchSignal
    match_strength: MatchStrength
    score: float
    confidence: float
    matched_skill: str | None = None
    evidence: tuple[MatchEvidence, ...] = field(default_factory=tuple)
    explanation: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be in [0.0, 1.0], got {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")


@dataclass(frozen=True)
class Gap:
    requirement_type: RequirementType
    priority: RequirementPriority
    raw_text: str
    reason: str
    evidence_status: str
    related_candidate_skills: tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 1.0


@dataclass(frozen=True)
class DimensionScore:
    """One dimension's contribution to the overall score - the weight is
    carried alongside the score so the frontend/API can show "why this
    dimension counts for this much" without re-reading MatchingWeights.
    """

    name: str
    score: float
    weight: float
    evaluation_count: int


@dataclass(frozen=True)
class ScoreBreakdown:
    overall: float
    skills: float
    experience: float
    seniority: float
    education: float
    certifications: float
    languages: float
    responsibilities: float
    domain: float
    mandatory_gap_penalty: float
    dimensions: tuple[DimensionScore, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ATSAnalysis:
    candidate_document_id: str
    job_document_id: str
    engine_version: str
    status: AnalysisStatus
    overall_score: float | None = None
    score_breakdown: ScoreBreakdown | None = None
    requirement_evaluations: tuple[RequirementEvaluation, ...] = field(default_factory=tuple)
    gaps: tuple[Gap, ...] = field(default_factory=tuple)
    metadata: dict = field(default_factory=dict)
