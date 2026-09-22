"""Responsibility / role-alignment matching (section 16 of the Phase 4
brief). Deliberately lightweight: lexical word overlap first, an
optional pre-computed semantic score second (the application layer only
computes an embedding when lexical overlap is low - domain/ never calls
an embedding provider directly). This is supporting evidence, not a
skill-equivalent signal - see domain/matching/weights.py for why its
dimension weight stays modest.

A pure semantic match (no lexical overlap) never carries a `MatchEvidence`
- section 9: "a semantic match without evidence must not be treated as a
strong qualification." The explanation names the closest experience
by label only; the frontend must present this as inferred, not quoted.
"""
import re
from dataclasses import dataclass

from domain.cv.entities import Experience
from domain.job.enums import RequirementType
from domain.matching.entities import MatchEvidence, RequirementEvaluation
from domain.matching.enums import MatchSignal, RequirementPriority, RequirementStatus
from domain.matching.strength import SCORE_FOR_STRENGTH, confidence_for_signal, strength_for_signal
from domain.matching.weights import SemanticMatchingConfig

_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "using", "our", "your", "you", "we", "will", "be", "as", "is", "are",
    "this", "that", "have", "has", "who", "into", "across", "per",
}
_LEXICAL_OVERLAP_THRESHOLD = 0.25


@dataclass(frozen=True)
class BestLexicalMatch:
    overlap: float
    experience: Experience | None


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in _STOPWORDS and len(word) > 2}


def lexical_overlap(a: str, b: str) -> float:
    tokens_a, tokens_b = _tokenize(a), _tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def best_lexical_match(responsibility: str, experiences: tuple[Experience, ...]) -> BestLexicalMatch:
    best_overlap, best_experience = 0.0, None
    for experience in experiences:
        text = " ".join(filter(None, [experience.description, *experience.achievements]))
        overlap = lexical_overlap(responsibility, text)
        if overlap > best_overlap:
            best_overlap, best_experience = overlap, experience
    return BestLexicalMatch(overlap=best_overlap, experience=best_experience)


def _experience_label(experience: Experience) -> str:
    parts = [part for part in (experience.title, experience.company) if part]
    return " at ".join(parts) if parts else "an experience entry"


def evaluate_responsibility(
    responsibility_text: str,
    experiences: tuple[Experience, ...],
    *,
    semantic_score: float | None = None,
    semantic_match_experience: Experience | None = None,
    semantic_config: SemanticMatchingConfig | None = None,
) -> RequirementEvaluation:
    lexical = best_lexical_match(responsibility_text, experiences)

    config = semantic_config or SemanticMatchingConfig()

    if lexical.overlap >= _LEXICAL_OVERLAP_THRESHOLD and lexical.experience is not None:
        signal = MatchSignal.PARTIAL_MATCH
        label = _experience_label(lexical.experience)
        explanation = f"Overlapping terms found with {label}."
        evidence = (
            (
                MatchEvidence(
                    evidence=lexical.experience.evidence, source_type="EXPERIENCE", source_label=label
                ),
            )
            if lexical.experience.evidence is not None
            else ()
        )
    elif semantic_score is not None and semantic_score >= config.partial_threshold:
        signal = MatchSignal.SEMANTIC_MATCH
        label = _experience_label(semantic_match_experience) if semantic_match_experience else "an experience"
        explanation = f"No direct wording overlap, but conceptually similar to {label}."
        evidence = ()
    else:
        signal = MatchSignal.NO_EVIDENCE
        explanation = "No comparable experience or project description found."
        evidence = ()

    status = (
        RequirementStatus.PARTIALLY_MET if signal != MatchSignal.NO_EVIDENCE else RequirementStatus.NOT_MET
    )
    strength = strength_for_signal(signal, semantic_score=semantic_score)
    return RequirementEvaluation(
        requirement_type=RequirementType.RESPONSIBILITY,
        priority=RequirementPriority.OPTIONAL,
        raw_text=responsibility_text,
        status=status,
        match_signal=signal,
        match_strength=strength,
        score=SCORE_FOR_STRENGTH[strength],
        confidence=confidence_for_signal(signal, semantic_score=semantic_score),
        evidence=evidence,
        explanation=explanation,
    )
