"""Hybrid skill requirement matching (sections 7-9 of the Phase 4 brief).

Four layers, tried in order, the first that resolves the requirement
wins:

    1. Exact / alias lexical match  - candidate has the exact canonical
       skill (Phase 2's normalize_skill_name already resolved both sides'
       aliases to canonical names before this module ever runs - see the
       module docstring below for why ALIAS_MATCH can still be
       distinguished from EXACT_MATCH here).
    2. Ontology match - domain.skills.relationships.build_relationship_view
       finds a related skill (parent/child/ecosystem/explicit) the
       candidate does have.
    3. Semantic match - only attempted by the caller (application layer)
       when neither of the above resolved the requirement; this module
       only classifies an already-computed similarity score
       (domain/ never calls an embedding provider directly).
    4. No evidence.

Why ALIAS_MATCH can still appear here even though Phase 2 already
normalizes aliases: `requirement.skill`/a candidate's resolved
`CandidateSkillMention.skill` are canonical either way, but the ORIGINAL
surface text ("Postgres" vs "PostgreSQL") is still available on
`requirement.raw_text` / `CandidateSkillSignal.raw_text`. If either side's
original text was an alias rather than the canonical spelling, the match
is reported as ALIAS_MATCH - a real distinction for the explanation UI,
even though both signals resolve to the same strength (STRONG - see
domain/matching/strength.py's rationale: an alias is the same skill, not
a weaker claim).
"""
from domain.job.entities import JobRequirement
from domain.matching.candidate_index import (
    CandidateSkillSignal,
    is_alias_surface_form,
)
from domain.matching.entities import MatchEvidence, RequirementEvaluation
from domain.matching.enums import MatchSignal, RequirementStatus
from domain.matching.priority import priority_from_importance
from domain.matching.strength import (
    SCORE_FOR_STRENGTH,
    confidence_for_signal,
    strength_for_signal,
)
from domain.matching.weights import SemanticMatchingConfig
from domain.skills.entities import Skill
from domain.skills.relationships import build_relationship_view


def evaluate_skill_requirement(
    requirement: JobRequirement,
    candidate_index: dict[str, list[CandidateSkillSignal]],
    all_skills: list[Skill],
    *,
    semantic_score: float | None = None,
    semantic_config: SemanticMatchingConfig | None = None,
) -> RequirementEvaluation:
    priority = priority_from_importance(requirement.importance)
    required_skill = requirement.skill

    if required_skill is None:
        return _evaluate_unresolved_requirement(requirement, priority, candidate_index)

    exact_signals = candidate_index.get(required_skill.canonical_name)
    if exact_signals:
        is_alias = is_alias_surface_form(requirement.raw_text, required_skill.canonical_name) or any(
            is_alias_surface_form(signal.raw_text, required_skill.canonical_name) for signal in exact_signals
        )
        signal = MatchSignal.ALIAS_MATCH if is_alias else MatchSignal.EXACT_MATCH
        return _build_evaluation(
            requirement,
            priority,
            signal=signal,
            evidence_signals=exact_signals,
            matched_skill=required_skill.canonical_name,
            explanation=f"Candidate demonstrates {required_skill.canonical_name} directly.",
        )

    view = build_relationship_view(required_skill, all_skills)
    for related in view.all_related:
        related_signals = candidate_index.get(related.skill.canonical_name)
        if related_signals:
            return _build_evaluation(
                requirement,
                priority,
                signal=MatchSignal.RELATED_MATCH,
                evidence_signals=related_signals,
                matched_skill=related.skill.canonical_name,
                explanation=(
                    f"{required_skill.canonical_name} itself is not evidenced. Candidate demonstrates "
                    f"{related.skill.canonical_name} "
                    f"({related.relation_type.value.replace('_', ' ').lower()})."
                ),
            )

    if semantic_score is not None:
        config = semantic_config or SemanticMatchingConfig()
        if semantic_score >= config.partial_threshold:
            return _build_evaluation(
                requirement,
                priority,
                signal=MatchSignal.SEMANTIC_MATCH,
                evidence_signals=[],
                matched_skill=None,
                explanation=(
                    f"No direct or related evidence of {required_skill.canonical_name}. "
                    "A semantically similar concept was found in the candidate's experience text."
                ),
                semantic_score=semantic_score,
            )

    return _build_evaluation(
        requirement,
        priority,
        signal=MatchSignal.NO_EVIDENCE,
        evidence_signals=[],
        matched_skill=None,
        explanation=f"No evidence of {required_skill.canonical_name} or a related skill.",
    )


def _evaluate_unresolved_requirement(
    requirement: JobRequirement, priority, candidate_index: dict[str, list[CandidateSkillSignal]]
) -> RequirementEvaluation:
    """`requirement.skill` is None only when Phase 2's own alias index
    could not resolve the requirement's raw text to a taxonomy entry -
    the candidate side is equally unresolvable by identity, so the best
    this layer can do is a case-insensitive substring check.
    """
    needle = requirement.raw_text.strip().lower()
    for canonical_name, signals in candidate_index.items():
        if needle and needle in canonical_name.lower():
            return _build_evaluation(
                requirement,
                priority,
                signal=MatchSignal.PARTIAL_MATCH,
                evidence_signals=signals,
                matched_skill=canonical_name,
                explanation=f"'{requirement.raw_text}' is not in the taxonomy; a textual overlap was found.",
            )
    return _build_evaluation(
        requirement,
        priority,
        signal=MatchSignal.NO_EVIDENCE,
        evidence_signals=[],
        matched_skill=None,
        explanation=f"'{requirement.raw_text}' is not in the taxonomy and no textual overlap was found.",
    )


def _build_evaluation(
    requirement: JobRequirement,
    priority,
    *,
    signal: MatchSignal,
    evidence_signals: list[CandidateSkillSignal],
    matched_skill: str | None,
    explanation: str,
    semantic_score: float | None = None,
) -> RequirementEvaluation:
    strength = strength_for_signal(signal, semantic_score=semantic_score)
    status = (
        RequirementStatus.NOT_MET
        if signal == MatchSignal.NO_EVIDENCE
        else RequirementStatus.MET
        if signal in (MatchSignal.EXACT_MATCH, MatchSignal.ALIAS_MATCH)
        else RequirementStatus.PARTIALLY_MET
    )
    evidence = tuple(
        MatchEvidence(evidence=item.evidence, source_type=item.source_type, source_label=item.source_label)
        for item in evidence_signals
        if item.evidence is not None
    )
    return RequirementEvaluation(
        requirement_type=requirement.requirement_type,
        priority=priority,
        raw_text=requirement.raw_text,
        status=status,
        match_signal=signal,
        match_strength=strength,
        score=SCORE_FOR_STRENGTH[strength],
        confidence=confidence_for_signal(signal, semantic_score=semantic_score),
        matched_skill=matched_skill,
        evidence=evidence,
        explanation=explanation,
    )
