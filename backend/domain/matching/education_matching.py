"""Education requirement matching (section 13 of the Phase 4 brief).
Compares `JobRequirement.normalized_value` (an `EducationLevel` string,
from Phase 3's requirement enrichment) against the highest
`Education.degree_level` the candidate's CV evidences. Never infers a
degree the CV does not state.
"""
from domain.cv.education_normalization import EducationLevel
from domain.cv.entities import CandidateProfile, Education
from domain.job.entities import JobRequirement
from domain.matching.entities import MatchEvidence, RequirementEvaluation
from domain.matching.enums import EducationComparison, MatchSignal, RequirementStatus
from domain.matching.priority import priority_from_importance
from domain.matching.strength import SCORE_FOR_STRENGTH, confidence_for_signal, strength_for_signal

# PROFESSIONAL_CERTIFICATE is not an academic degree tier - excluded from
# the ladder rather than force-ranked against Bachelor's/Master's.
_ORDER: tuple[EducationLevel, ...] = (
    EducationLevel.HIGH_SCHOOL,
    EducationLevel.ASSOCIATE,
    EducationLevel.BACHELOR,
    EducationLevel.MASTER,
    EducationLevel.DOCTORATE,
)


def _rank(level: EducationLevel) -> int | None:
    return _ORDER.index(level) if level in _ORDER else None


def candidate_highest_education(profile: CandidateProfile) -> tuple[EducationLevel, Education | None]:
    ranked = [
        (_rank(entry.degree_level), entry.degree_level, entry)
        for entry in profile.education
        if entry.degree_level and _rank(entry.degree_level) is not None
    ]
    if not ranked:
        return EducationLevel.UNKNOWN, None
    _, level, entry = max(ranked, key=lambda item: item[0])
    return level, entry


def compare_education(required: EducationLevel, candidate: EducationLevel) -> EducationComparison:
    if candidate == EducationLevel.UNKNOWN:
        return EducationComparison.UNKNOWN
    required_rank, candidate_rank = _rank(required), _rank(candidate)
    if required_rank is None or candidate_rank is None:
        return EducationComparison.UNKNOWN
    if candidate_rank >= required_rank:
        return EducationComparison.MEETS if candidate_rank == required_rank else EducationComparison.EXCEEDS
    return EducationComparison.BELOW


_COMPARISON_TO_SIGNAL: dict[EducationComparison, MatchSignal] = {
    EducationComparison.MEETS: MatchSignal.EXACT_MATCH,
    EducationComparison.EXCEEDS: MatchSignal.EXACT_MATCH,
    EducationComparison.BELOW: MatchSignal.PARTIAL_MATCH,
    EducationComparison.UNKNOWN: MatchSignal.NO_EVIDENCE,
}


def evaluate_education_requirement(
    requirement: JobRequirement, profile: CandidateProfile
) -> RequirementEvaluation:
    priority = priority_from_importance(requirement.importance)
    required_level = EducationLevel(requirement.normalized_value) if requirement.normalized_value else None

    if required_level is None:
        return _evaluation(
            requirement,
            priority,
            signal=MatchSignal.NO_EVIDENCE,
            status=RequirementStatus.UNKNOWN,
            evidence_entry=None,
            explanation="The required education level could not be determined from the job offer text.",
        )

    candidate_level, entry = candidate_highest_education(profile)
    comparison = compare_education(required_level, candidate_level)
    signal = _COMPARISON_TO_SIGNAL[comparison]
    status = (
        RequirementStatus.UNKNOWN
        if comparison == EducationComparison.UNKNOWN
        else RequirementStatus.MET
        if comparison in (EducationComparison.MEETS, EducationComparison.EXCEEDS)
        else RequirementStatus.PARTIALLY_MET
    )
    candidate_label = candidate_level.value.title()
    required_label = required_level.value.title()
    explanation = {
        EducationComparison.MEETS: (
            f"Candidate holds a {candidate_label} qualification, meeting the requirement."
        ),
        EducationComparison.EXCEEDS: (
            f"Candidate holds a {candidate_label} qualification, exceeding the requirement."
        ),
        EducationComparison.BELOW: (
            f"Candidate's highest qualification ({candidate_label}) is below the required {required_label}."
        ),
        EducationComparison.UNKNOWN: "No education level could be determined from the CV.",
    }[comparison]

    return _evaluation(
        requirement,
        priority,
        signal=signal,
        status=status,
        evidence_entry=entry,
        explanation=explanation,
    )


def _evaluation(
    requirement: JobRequirement,
    priority,
    *,
    signal: MatchSignal,
    status: RequirementStatus,
    evidence_entry: Education | None,
    explanation: str,
) -> RequirementEvaluation:
    strength = strength_for_signal(signal)
    evidence = ()
    if evidence_entry is not None and evidence_entry.evidence is not None:
        evidence = (
            MatchEvidence(
                evidence=evidence_entry.evidence,
                source_type="EDUCATION",
                source_label=evidence_entry.institution,
            ),
        )
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
