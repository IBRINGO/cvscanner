"""Language requirement matching (section 14 of the Phase 4 brief).

`domain.job.enums.RequirementType.LANGUAGE` exists but the current
rule-based job extractor (infrastructure/document_processing/extraction/
job_extractor.py) does not yet classify any line as a language
requirement - see docs/architecture/phase-4-matching.md "Known
limitations". This matcher is written and tested against the enum
regardless, so a future extractor enhancement (or a manually-created
requirement) is matched correctly the day it starts appearing.
"""
from domain.cv.entities import CandidateProfile, Language
from domain.cv.language_normalization import (
    LanguageProficiency,
    normalize_language_name,
    normalize_proficiency,
)
from domain.job.entities import JobRequirement
from domain.matching.entities import MatchEvidence, RequirementEvaluation
from domain.matching.enums import MatchSignal, ProficiencyComparison, RequirementStatus
from domain.matching.priority import priority_from_importance
from domain.matching.strength import SCORE_FOR_STRENGTH, confidence_for_signal, strength_for_signal

_ORDER: tuple[LanguageProficiency, ...] = (
    LanguageProficiency.BEGINNER,
    LanguageProficiency.ELEMENTARY,
    LanguageProficiency.INTERMEDIATE,
    LanguageProficiency.UPPER_INTERMEDIATE,
    LanguageProficiency.ADVANCED,
    LanguageProficiency.FLUENT,
    LanguageProficiency.NATIVE,
)


def _rank(level: LanguageProficiency) -> int | None:
    return _ORDER.index(level) if level in _ORDER else None


def find_candidate_language(profile: CandidateProfile, canonical_name: str) -> Language | None:
    for language in profile.languages:
        name = language.canonical_name or normalize_language_name(language.name)
        if name == canonical_name:
            return language
    return None


def compare_proficiency(
    required: LanguageProficiency | None, candidate: Language | None
) -> ProficiencyComparison:
    if candidate is None:
        return ProficiencyComparison.ABSENT
    candidate_level = candidate.proficiency_normalized or normalize_proficiency(candidate.proficiency)
    if candidate_level is None or candidate_level == LanguageProficiency.UNKNOWN:
        return ProficiencyComparison.PRESENT_UNKNOWN_LEVEL
    if required is None or required == LanguageProficiency.UNKNOWN:
        return ProficiencyComparison.PRESENT_UNKNOWN_LEVEL
    required_rank, candidate_rank = _rank(required), _rank(candidate_level)
    if required_rank is None or candidate_rank is None:
        return ProficiencyComparison.PRESENT_UNKNOWN_LEVEL
    if candidate_rank == required_rank:
        return ProficiencyComparison.EXACT
    return ProficiencyComparison.HIGHER if candidate_rank > required_rank else ProficiencyComparison.LOWER


_COMPARISON_TO_SIGNAL: dict[ProficiencyComparison, MatchSignal] = {
    ProficiencyComparison.EXACT: MatchSignal.EXACT_MATCH,
    ProficiencyComparison.HIGHER: MatchSignal.EXACT_MATCH,
    ProficiencyComparison.LOWER: MatchSignal.PARTIAL_MATCH,
    ProficiencyComparison.PRESENT_UNKNOWN_LEVEL: MatchSignal.PARTIAL_MATCH,
    ProficiencyComparison.ABSENT: MatchSignal.NO_EVIDENCE,
}


def evaluate_language_requirement(
    requirement: JobRequirement, profile: CandidateProfile
) -> RequirementEvaluation:
    priority = priority_from_importance(requirement.importance)
    required_name, required_level = _parse_requirement_text(requirement.raw_text)
    candidate_language = find_candidate_language(profile, required_name) if required_name else None
    comparison = compare_proficiency(required_level, candidate_language)
    signal = _COMPARISON_TO_SIGNAL[comparison]
    status = (
        RequirementStatus.MET
        if comparison in (ProficiencyComparison.EXACT, ProficiencyComparison.HIGHER)
        else RequirementStatus.PARTIALLY_MET
        if comparison in (ProficiencyComparison.LOWER, ProficiencyComparison.PRESENT_UNKNOWN_LEVEL)
        else RequirementStatus.NOT_MET
    )
    explanation = {
        ProficiencyComparison.EXACT: f"Candidate's {required_name} proficiency matches the requirement.",
        ProficiencyComparison.HIGHER: f"Candidate's {required_name} proficiency exceeds the requirement.",
        ProficiencyComparison.LOWER: f"Candidate lists {required_name} at a lower proficiency than required.",
        ProficiencyComparison.PRESENT_UNKNOWN_LEVEL: (
            f"Candidate lists {required_name} but no proficiency level is evidenced."
        ),
        ProficiencyComparison.ABSENT: f"No evidence of {required_name or requirement.raw_text} in the CV.",
    }[comparison]

    strength = strength_for_signal(signal)
    evidence = ()
    if candidate_language is not None and candidate_language.evidence is not None:
        evidence = (MatchEvidence(evidence=candidate_language.evidence, source_type="LANGUAGE"),)

    return RequirementEvaluation(
        requirement_type=requirement.requirement_type,
        priority=priority,
        raw_text=requirement.raw_text,
        status=status,
        match_signal=signal,
        match_strength=strength,
        score=SCORE_FOR_STRENGTH[strength],
        confidence=confidence_for_signal(signal),
        evidence=evidence,
        explanation=explanation,
    )


_PROFICIENCY_TOKENS = {
    "a1": LanguageProficiency.BEGINNER,
    "a2": LanguageProficiency.ELEMENTARY,
    "b1": LanguageProficiency.INTERMEDIATE,
    "b2": LanguageProficiency.UPPER_INTERMEDIATE,
    "c1": LanguageProficiency.ADVANCED,
    "c2": LanguageProficiency.FLUENT,
    "native": LanguageProficiency.NATIVE,
    "fluent": LanguageProficiency.FLUENT,
}


def _parse_requirement_text(raw_text: str) -> tuple[str | None, LanguageProficiency | None]:
    tokens = raw_text.replace("-", " ").split()
    if not tokens:
        return None, None
    level = None
    name_tokens = []
    for token in tokens:
        key = token.strip().lower()
        if key in _PROFICIENCY_TOKENS:
            level = _PROFICIENCY_TOKENS[key]
        else:
            name_tokens.append(token)
    name = normalize_language_name(" ".join(name_tokens)) if name_tokens else None
    return name, level
