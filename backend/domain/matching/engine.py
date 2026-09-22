"""Deterministic scoring and gap detection (sections 19-24 of the Phase
4 brief). Pure aggregation over already-computed `RequirementEvaluation`
objects - the per-dimension matchers (skill_matching.py,
experience_matching.py, ...) do the actual signal resolution; this module
only combines their results.

## Missing-dimension handling

A dimension with zero evaluations (e.g. a job posting states no
certification requirements at all) is excluded from the weighted
average rather than scored as 1.0 (would fabricate an achievement) or
0.0 (would punish the candidate for something never asked). Its weight
is redistributed proportionally across the dimensions that do have data,
via `present_weight_total` below.

## Mandatory requirement penalty (section 21)

A missing MANDATORY requirement subtracts `mandatory_penalty_per_gap`
from the overall score, capped at `mandatory_penalty_cap` (see
domain/matching/weights.py) - explicitly not a hard override to zero,
so the analysis stays explainable ("overall score + mandatory gaps +
supporting matches", per the brief).
"""
from domain.matching.entities import DimensionScore, Gap, RequirementEvaluation, ScoreBreakdown
from domain.matching.enums import MatchSignal, RequirementPriority, RequirementStatus
from domain.matching.weights import DEFAULT_WEIGHTS, MatchingWeights

_GAP_STATUSES = (RequirementStatus.NOT_MET, RequirementStatus.PARTIALLY_MET, RequirementStatus.UNKNOWN)


def _dimension_average(evaluations: tuple[RequirementEvaluation, ...]) -> float | None:
    if not evaluations:
        return None
    return sum(evaluation.score for evaluation in evaluations) / len(evaluations)


def compute_score_breakdown(
    *,
    skills: tuple[RequirementEvaluation, ...],
    experience: tuple[RequirementEvaluation, ...],
    seniority: tuple[RequirementEvaluation, ...],
    education: tuple[RequirementEvaluation, ...],
    certifications: tuple[RequirementEvaluation, ...],
    languages: tuple[RequirementEvaluation, ...],
    responsibilities: tuple[RequirementEvaluation, ...],
    domain: tuple[RequirementEvaluation, ...],
    weights: MatchingWeights = DEFAULT_WEIGHTS,
) -> ScoreBreakdown:
    dimension_evaluations = {
        "skills": skills,
        "experience": experience,
        "seniority": seniority,
        "education": education,
        "certifications": certifications,
        "languages": languages,
        "responsibilities": responsibilities,
        "domain": domain,
    }
    weight_map = weights.as_dict()

    scores: dict[str, float | None] = {}
    dimensions: list[DimensionScore] = []
    weighted_sum = 0.0
    present_weight_total = 0.0

    for name, evaluations in dimension_evaluations.items():
        score = _dimension_average(evaluations)
        scores[name] = score
        weight = weight_map[name]
        if score is not None:
            weighted_sum += score * weight
            present_weight_total += weight
        dimensions.append(
            DimensionScore(
                name=name,
                score=score if score is not None else 0.0,
                weight=weight,
                evaluation_count=len(evaluations),
            )
        )

    base_overall = (weighted_sum / present_weight_total) if present_weight_total > 0 else 0.0

    all_evaluations = [e for evaluations in dimension_evaluations.values() for e in evaluations]
    mandatory_gaps = sum(
        1
        for evaluation in all_evaluations
        if evaluation.priority == RequirementPriority.MANDATORY
        and evaluation.status == RequirementStatus.NOT_MET
    )
    penalty = min(weights.mandatory_penalty_cap, mandatory_gaps * weights.mandatory_penalty_per_gap)
    overall = max(0.0, base_overall - penalty)

    return ScoreBreakdown(
        overall=round(overall, 4),
        skills=round(scores["skills"] or 0.0, 4),
        experience=round(scores["experience"] or 0.0, 4),
        seniority=round(scores["seniority"] or 0.0, 4),
        education=round(scores["education"] or 0.0, 4),
        certifications=round(scores["certifications"] or 0.0, 4),
        languages=round(scores["languages"] or 0.0, 4),
        responsibilities=round(scores["responsibilities"] or 0.0, 4),
        domain=round(scores["domain"] or 0.0, 4),
        mandatory_gap_penalty=round(penalty, 4),
        dimensions=tuple(dimensions),
    )


def detect_gaps(evaluations: tuple[RequirementEvaluation, ...]) -> tuple[Gap, ...]:
    gaps = []
    for evaluation in evaluations:
        if evaluation.status not in _GAP_STATUSES:
            continue
        evidence_status = (
            "NO_EVIDENCE" if evaluation.match_signal == MatchSignal.NO_EVIDENCE else "PARTIAL_EVIDENCE"
        )
        related_skills = tuple(
            dict.fromkeys(
                label
                for item in evaluation.evidence
                if (label := item.source_label) is not None
            )
        )
        if not related_skills and evaluation.matched_skill:
            related_skills = (evaluation.matched_skill,)
        gaps.append(
            Gap(
                requirement_type=evaluation.requirement_type,
                priority=evaluation.priority,
                raw_text=evaluation.raw_text,
                reason=evaluation.explanation,
                evidence_status=evidence_status,
                related_candidate_skills=related_skills,
                confidence=evaluation.confidence,
            )
        )
    return tuple(gaps)
