"""Deterministic recommendation generation (Phase 5 sections 6-13).

Every recommendation originates from an actual Phase 4 finding - a
specific `RequirementEvaluation` this analysis already produced. This
module never asks an LLM to invent advice and never generates generic
career guidance unrelated to the job being analyzed (section 6). It
also never claims a specific score improvement (section 13) - impact is
a qualitative "how relevant is this to the current analysis" label,
not a promise.

Confidence is derived directly from `RequirementEvaluation.confidence`
(the same matching-method confidence Phase 4 already computes - see
domain/documents/evidence.py's module docstring for what that number
does and does not mean) rather than inventing a second, disconnected
scale.
"""
from dataclasses import dataclass

from domain.job.enums import RequirementType
from domain.matching.entities import RequirementEvaluation
from domain.matching.enums import MatchSignal, RequirementPriority, RequirementStatus
from domain.recommendations.config import DEFAULT_CONFIG, RecommendationEngineConfig
from domain.recommendations.entities import Recommendation
from domain.recommendations.enums import (
    RecommendationConfidence,
    RecommendationImpact,
    RecommendationPriority,
    RecommendationSafety,
    RecommendationType,
)

# Requirement types this engine never comments on directly - domain
# alignment and unclassified requirements are structural, supporting
# signals (Phase 4 sections 12/13), not something rewording a bullet can
# meaningfully address (section 6: no generic advice unrelated to a
# specific, actionable finding).
_SKIPPED_REQUIREMENT_TYPES = (RequirementType.OTHER,)

_SKILL_REQUIREMENT_TYPES = (RequirementType.REQUIRED_SKILL, RequirementType.PREFERRED_SKILL)


def _confidence_from_score(score: float, config: RecommendationEngineConfig) -> RecommendationConfidence:
    if score >= config.high_confidence_threshold:
        return RecommendationConfidence.HIGH
    if score >= config.medium_confidence_threshold:
        return RecommendationConfidence.MEDIUM
    return RecommendationConfidence.LOW


def _priority_for_gap(
    requirement_priority: RequirementPriority, is_total_absence: bool
) -> RecommendationPriority:
    """A missing/absent finding on a MANDATORY requirement is always
    CRITICAL - section 8: prioritization must reflect mandatory status,
    not keyword frequency. A PREFERRED requirement's total absence is
    HIGH; a partial/weak finding on it is MEDIUM. OPTIONAL requirements
    (currently only RESPONSIBILITY) never rise above MEDIUM.
    """
    if requirement_priority == RequirementPriority.MANDATORY:
        return RecommendationPriority.CRITICAL if is_total_absence else RecommendationPriority.HIGH
    if requirement_priority == RequirementPriority.PREFERRED:
        return RecommendationPriority.HIGH if is_total_absence else RecommendationPriority.MEDIUM
    return RecommendationPriority.MEDIUM if is_total_absence else RecommendationPriority.LOW


def _impact_for_priority(priority: RecommendationPriority) -> RecommendationImpact:
    if priority in (RecommendationPriority.CRITICAL, RecommendationPriority.HIGH):
        return RecommendationImpact.HIGH_IMPACT
    if priority == RecommendationPriority.MEDIUM:
        return RecommendationImpact.MEDIUM_IMPACT
    return RecommendationImpact.LOW_IMPACT


@dataclass(frozen=True)
class _Candidate:
    """An internal, pre-recommendation shape used only to make
    deduplication (section 12) and the concise-action-plan cap
    (section 13/44) simple: sort, cap, drop, then convert survivors to
    real Recommendation objects.
    """

    recommendation: Recommendation
    sort_key: tuple[int, int]


_PRIORITY_RANK = {
    RecommendationPriority.CRITICAL: 0,
    RecommendationPriority.HIGH: 1,
    RecommendationPriority.MEDIUM: 2,
    RecommendationPriority.LOW: 3,
}


def generate_recommendations(
    evaluations: tuple[RequirementEvaluation, ...],
    config: RecommendationEngineConfig = DEFAULT_CONFIG,
) -> tuple[Recommendation, ...]:
    candidates: list[_Candidate] = []

    for index, evaluation in enumerate(evaluations):
        if evaluation.requirement_type in _SKIPPED_REQUIREMENT_TYPES:
            continue
        if evaluation.status == RequirementStatus.MET and evaluation.match_signal not in (
            MatchSignal.ALIAS_MATCH,
        ):
            # A fully MET requirement needs no recommendation, except the
            # one case where a fully-met requirement still has a
            # keyword-placement opportunity (section 22: an ALIAS_MATCH
            # means the CV uses a non-canonical surface form).
            continue

        recommendation = _recommendation_for(evaluation, index, config)
        if recommendation is None:
            continue
        candidates.append(
            _Candidate(
                recommendation=recommendation,
                sort_key=(_PRIORITY_RANK[recommendation.priority], index),
            )
        )

    return _deduplicate_and_cap(candidates, config)


def _deduplicate_and_cap(
    candidates: list[_Candidate], config: RecommendationEngineConfig
) -> tuple[Recommendation, ...]:
    # Deduplicate by (type, title): keep the first (highest-priority,
    # since candidates are about to be sorted) occurrence - section 12.
    candidates.sort(key=lambda c: c.sort_key)
    seen: set[tuple[RecommendationType, str]] = set()
    deduplicated: list[Recommendation] = []
    for candidate in candidates:
        key = (candidate.recommendation.type, candidate.recommendation.title)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(candidate.recommendation)

    critical_and_high = [
        r
        for r in deduplicated
        if r.priority in (RecommendationPriority.CRITICAL, RecommendationPriority.HIGH)
    ]
    rest = [
        r
        for r in deduplicated
        if r.priority not in (RecommendationPriority.CRITICAL, RecommendationPriority.HIGH)
    ]
    return tuple(critical_and_high + rest[: config.max_medium_or_lower_recommendations])


def _recommendation_for(
    evaluation: RequirementEvaluation, index: int, config: RecommendationEngineConfig
) -> Recommendation | None:
    if evaluation.requirement_type in _SKILL_REQUIREMENT_TYPES:
        return _skill_recommendation(evaluation, index, config)
    if evaluation.requirement_type == RequirementType.EXPERIENCE:
        return _experience_recommendation(evaluation, index, config)
    if evaluation.requirement_type == RequirementType.EDUCATION:
        return _missing_requirement_recommendation(
            evaluation, index, config, title=f"Missing education requirement: {evaluation.raw_text}"
        )
    if evaluation.requirement_type == RequirementType.CERTIFICATION:
        return _certification_recommendation(evaluation, index, config)
    if evaluation.requirement_type == RequirementType.LANGUAGE:
        return _language_recommendation(evaluation, index, config)
    if evaluation.requirement_type == RequirementType.SENIORITY:
        return _seniority_recommendation(evaluation, index, config)
    if evaluation.requirement_type == RequirementType.RESPONSIBILITY:
        return _responsibility_recommendation(evaluation, index, config)
    return None


def _skill_recommendation(
    evaluation: RequirementEvaluation, index: int, config: RecommendationEngineConfig
) -> Recommendation | None:
    if evaluation.match_signal == MatchSignal.NO_EVIDENCE:
        return _missing_requirement_recommendation(
            evaluation, index, config, title=f"Missing skill: {evaluation.raw_text}"
        )
    if evaluation.match_signal in (
        MatchSignal.RELATED_MATCH,
        MatchSignal.SEMANTIC_MATCH,
        MatchSignal.PARTIAL_MATCH,
    ):
        priority = _priority_for_gap(evaluation.priority, is_total_absence=False)
        return Recommendation(
            type=RecommendationType.UNDERREPRESENTED_SKILL,
            priority=priority,
            confidence=_confidence_from_score(evaluation.confidence, config),
            safety=RecommendationSafety.REQUIRES_CANDIDATE_CONFIRMATION,
            impact=_impact_for_priority(priority),
            title=f"Clarify {evaluation.raw_text} experience",
            summary=(
                f"The job asks for {evaluation.raw_text}. {evaluation.explanation}"
            ),
            reason=evaluation.explanation,
            suggested_action=(
                f"If you have hands-on {evaluation.raw_text} experience, add it explicitly - "
                "CVScanner cannot add it for you without evidence."
            ),
            related_requirement_index=index,
            supporting_evidence=evaluation.evidence,
            current_state=evaluation.matched_skill,
            target_state=evaluation.raw_text,
        )
    if evaluation.match_signal == MatchSignal.ALIAS_MATCH:
        priority = RecommendationPriority.LOW
        return Recommendation(
            type=RecommendationType.KEYWORD_PLACEMENT,
            priority=priority,
            confidence=RecommendationConfidence.HIGH,
            safety=RecommendationSafety.SAFE_TO_REPHRASE,
            impact=RecommendationImpact.LOW_IMPACT,
            title=f"Use the canonical name for {evaluation.raw_text}",
            summary=(
                f"Your CV mentions a known alternate name for {evaluation.raw_text}. "
                "Using the exact term the job posting uses can improve ATS keyword matching."
            ),
            reason=evaluation.explanation,
            suggested_action=f"Normalize the wording to '{evaluation.matched_skill or evaluation.raw_text}'.",
            related_requirement_index=index,
            supporting_evidence=evaluation.evidence,
            current_state=evaluation.raw_text,
            target_state=evaluation.matched_skill,
        )
    return None


def _missing_requirement_recommendation(
    evaluation: RequirementEvaluation, index: int, config: RecommendationEngineConfig, *, title: str
) -> Recommendation:
    priority = _priority_for_gap(evaluation.priority, is_total_absence=True)
    return Recommendation(
        type=RecommendationType.MISSING_REQUIREMENT,
        priority=priority,
        confidence=_confidence_from_score(evaluation.confidence, config),
        safety=RecommendationSafety.NOT_SAFE_TO_AUTOMATE,
        impact=_impact_for_priority(priority),
        title=title,
        summary=evaluation.explanation,
        reason=evaluation.explanation,
        suggested_action=(
            "This cannot be added automatically. If you genuinely have this experience, "
            "add it to your CV yourself with real evidence; otherwise this remains a real gap."
        ),
        related_requirement_index=index,
        supporting_evidence=evaluation.evidence,
        target_state=evaluation.raw_text,
    )


def _experience_recommendation(
    evaluation: RequirementEvaluation, index: int, config: RecommendationEngineConfig
) -> Recommendation | None:
    if evaluation.status == RequirementStatus.NOT_MET:
        return _missing_requirement_recommendation(
            evaluation, index, config, title=f"Insufficient experience: {evaluation.raw_text}"
        )
    if evaluation.status == RequirementStatus.UNKNOWN:
        priority = RecommendationPriority.MEDIUM
        return Recommendation(
            type=RecommendationType.EXPERIENCE_CLARIFICATION,
            priority=priority,
            confidence=RecommendationConfidence.LOW,
            safety=RecommendationSafety.REQUIRES_CANDIDATE_CONFIRMATION,
            impact=_impact_for_priority(priority),
            title="Clarify experience dates",
            summary=(
                f"The job requires {evaluation.raw_text}, but the relevant experience entries "
                "have dates CVScanner could not confidently parse."
            ),
            reason=evaluation.explanation,
            suggested_action=(
                "Use an explicit date format (e.g. 'Jan 2020 - Present') so this can be assessed accurately."
            ),
            related_requirement_index=index,
            supporting_evidence=evaluation.evidence,
        )
    return None


def _certification_recommendation(
    evaluation: RequirementEvaluation, index: int, config: RecommendationEngineConfig
) -> Recommendation | None:
    if evaluation.status != RequirementStatus.MET:
        priority = _priority_for_gap(evaluation.priority, is_total_absence=True)
        return Recommendation(
            type=RecommendationType.CERTIFICATION_GAP,
            priority=priority,
            confidence=RecommendationConfidence.HIGH,
            safety=RecommendationSafety.NOT_SAFE_TO_AUTOMATE,
            impact=_impact_for_priority(priority),
            title=f"Missing certification: {evaluation.raw_text}",
            summary=evaluation.explanation,
            reason=evaluation.explanation,
            suggested_action=(
                "A certification can never be inferred from related skills. Only add this if you "
                "have actually earned it."
            ),
            related_requirement_index=index,
            supporting_evidence=evaluation.evidence,
            target_state=evaluation.raw_text,
        )
    return None


def _language_recommendation(
    evaluation: RequirementEvaluation, index: int, config: RecommendationEngineConfig
) -> Recommendation | None:
    if evaluation.status in (RequirementStatus.NOT_MET, RequirementStatus.PARTIALLY_MET):
        priority = _priority_for_gap(
            evaluation.priority, is_total_absence=evaluation.status == RequirementStatus.NOT_MET
        )
        return Recommendation(
            type=RecommendationType.LANGUAGE_GAP,
            priority=priority,
            confidence=_confidence_from_score(evaluation.confidence, config),
            safety=RecommendationSafety.NOT_SAFE_TO_AUTOMATE,
            impact=_impact_for_priority(priority),
            title=f"Language requirement not fully met: {evaluation.raw_text}",
            summary=evaluation.explanation,
            reason=evaluation.explanation,
            suggested_action=(
                "Proficiency levels can never be upgraded automatically - this stays a real gap."
            ),
            related_requirement_index=index,
            supporting_evidence=evaluation.evidence,
        )
    return None


def _seniority_recommendation(
    evaluation: RequirementEvaluation, index: int, config: RecommendationEngineConfig
) -> Recommendation | None:
    if evaluation.status in (RequirementStatus.NOT_MET, RequirementStatus.UNKNOWN):
        priority = RecommendationPriority.MEDIUM
        safety = (
            RecommendationSafety.NOT_SAFE_TO_AUTOMATE
            if evaluation.status == RequirementStatus.NOT_MET
            else RecommendationSafety.REQUIRES_CANDIDATE_CONFIRMATION
        )
        return Recommendation(
            type=RecommendationType.SENIORITY_CLARIFICATION,
            priority=priority,
            confidence=_confidence_from_score(evaluation.confidence, config),
            safety=safety,
            impact=_impact_for_priority(priority),
            title="Clarify seniority level",
            summary=evaluation.explanation,
            reason=evaluation.explanation,
            suggested_action=(
                "Make sure job titles and scope of responsibility clearly reflect your actual seniority."
            ),
            related_requirement_index=index,
            supporting_evidence=evaluation.evidence,
        )
    return None


def _responsibility_recommendation(
    evaluation: RequirementEvaluation, index: int, config: RecommendationEngineConfig
) -> Recommendation | None:
    if evaluation.status == RequirementStatus.PARTIALLY_MET:
        priority = RecommendationPriority.MEDIUM
        return Recommendation(
            type=RecommendationType.RESPONSIBILITY_ALIGNMENT,
            priority=priority,
            confidence=_confidence_from_score(evaluation.confidence, config),
            safety=RecommendationSafety.SAFE_TO_REPHRASE,
            impact=_impact_for_priority(priority),
            title=f"Make existing experience match: {evaluation.raw_text}",
            summary=evaluation.explanation,
            reason=evaluation.explanation,
            suggested_action=(
                "Consider rewording the relevant bullet to explicitly reflect this responsibility."
            ),
            related_requirement_index=index,
            supporting_evidence=evaluation.evidence,
        )
    if evaluation.status == RequirementStatus.NOT_MET:
        priority = RecommendationPriority.LOW
        return Recommendation(
            type=RecommendationType.RESPONSIBILITY_ALIGNMENT,
            priority=priority,
            confidence=RecommendationConfidence.LOW,
            safety=RecommendationSafety.NOT_SAFE_TO_AUTOMATE,
            impact=RecommendationImpact.LOW_IMPACT,
            title=f"No matching experience found: {evaluation.raw_text}",
            summary=evaluation.explanation,
            reason=evaluation.explanation,
            suggested_action="This responsibility has no comparable experience on the CV to draw from.",
            related_requirement_index=index,
            supporting_evidence=evaluation.evidence,
        )
    return None
