"""Single source of truth for mapping a `MatchSignal` (and, for semantic
matches, a similarity score) onto the normalized `MatchStrength` scale
(section 22 of the Phase 4 brief: "do not let multiple systems
independently invent their own match-strength scales").

Rationale for the mapping (section 8 of the brief: document, don't
invent, arbitrary orderings):

    EXACT_MATCH   -> STRONG   (the exact required term was found)
    ALIAS_MATCH   -> STRONG   (a known alias of the same skill is the
                               same skill under a different name, not a
                               weaker claim - "Postgres" IS PostgreSQL)
    RELATED_MATCH -> PARTIAL  (an ontology relative, e.g. Docker for a
                               Kubernetes requirement, is real evidence
                               of an adjacent skill, never proof of the
                               required one - section 7/12)
    SEMANTIC_MATCH-> GOOD or PARTIAL, scaled by the similarity score
                               against SemanticMatchingConfig - capped
                               below STRONG because a semantic signal
                               alone must never be presented as an exact
                               qualification (section 9)
    PARTIAL_MATCH -> WEAK     (some textual overlap, not a resolved
                               identity or relationship)
    NO_EVIDENCE   -> NONE
"""
from domain.matching.enums import MatchSignal, MatchStrength
from domain.matching.weights import SemanticMatchingConfig

_SIGNAL_STRENGTH: dict[MatchSignal, MatchStrength] = {
    MatchSignal.EXACT_MATCH: MatchStrength.STRONG,
    MatchSignal.ALIAS_MATCH: MatchStrength.STRONG,
    MatchSignal.RELATED_MATCH: MatchStrength.PARTIAL,
    MatchSignal.PARTIAL_MATCH: MatchStrength.WEAK,
    MatchSignal.NO_EVIDENCE: MatchStrength.NONE,
}


def strength_for_signal(
    signal: MatchSignal,
    *,
    semantic_score: float | None = None,
    config: SemanticMatchingConfig | None = None,
) -> MatchStrength:
    if signal != MatchSignal.SEMANTIC_MATCH:
        return _SIGNAL_STRENGTH[signal]

    config = config or SemanticMatchingConfig()
    if semantic_score is None:
        return MatchStrength.WEAK
    if semantic_score >= config.strong_threshold:
        return MatchStrength.GOOD
    if semantic_score >= config.partial_threshold:
        return MatchStrength.PARTIAL
    return MatchStrength.WEAK


# A per-requirement completeness score for each strength - used to
# aggregate individual RequirementEvaluations into a dimension score
# (domain/matching/scoring.py). One shared scale (section 22) rather than
# each matcher inventing its own numeric mapping.
SCORE_FOR_STRENGTH: dict[MatchStrength, float] = {
    MatchStrength.STRONG: 1.0,
    MatchStrength.GOOD: 0.75,
    MatchStrength.PARTIAL: 0.5,
    MatchStrength.WEAK: 0.25,
    MatchStrength.NONE: 0.0,
}

# How confident the engine is in its own determination (matching-method
# confidence, never a truth probability - same rule as
# domain/documents/evidence.py::Evidence.confidence). NO_EVIDENCE still
# carries a high confidence because "no evidence was found" is itself a
# reliable fact about the search, not an uncertain one.
CONFIDENCE_FOR_SIGNAL: dict[MatchSignal, float] = {
    MatchSignal.EXACT_MATCH: 0.98,
    MatchSignal.ALIAS_MATCH: 0.95,
    MatchSignal.RELATED_MATCH: 0.80,
    MatchSignal.PARTIAL_MATCH: 0.60,
    MatchSignal.NO_EVIDENCE: 0.90,
}


def confidence_for_signal(signal: MatchSignal, *, semantic_score: float | None = None) -> float:
    if signal == MatchSignal.SEMANTIC_MATCH:
        return min(0.90, semantic_score) if semantic_score is not None else 0.5
    return CONFIDENCE_FOR_SIGNAL[signal]
