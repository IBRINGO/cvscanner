"""Seniority requirement matching (section 12 of the Phase 4 brief).

`JobProfile.seniority_normalized` and `Experience.seniority` are both
`domain.cv.seniority.SeniorityLevel` values (Phase 3) - this module adds
only the ordinal comparison Phase 3 never needed. `UNKNOWN` on either
side is a distinct, legitimate outcome, never silently treated as
"does not meet" (explicit brief requirement).
"""
from domain.cv.entities import CandidateProfile
from domain.cv.seniority import SeniorityLevel
from domain.job.entities import JobProfile
from domain.job.enums import RequirementType
from domain.matching.entities import MatchEvidence, RequirementEvaluation
from domain.matching.enums import MatchSignal, RequirementPriority, RequirementStatus, SeniorityComparison
from domain.matching.strength import SCORE_FOR_STRENGTH, confidence_for_signal, strength_for_signal

_ORDER: tuple[SeniorityLevel, ...] = (
    SeniorityLevel.INTERN,
    SeniorityLevel.JUNIOR,
    SeniorityLevel.MID,
    SeniorityLevel.SENIOR,
    SeniorityLevel.LEAD,
    SeniorityLevel.MANAGER,
    SeniorityLevel.DIRECTOR,
    SeniorityLevel.EXECUTIVE,
)


def _rank(level: SeniorityLevel) -> int | None:
    return _ORDER.index(level) if level in _ORDER else None


def candidate_peak_seniority(profile: CandidateProfile) -> SeniorityLevel:
    """The highest seniority demonstrated across the candidate's
    experiences - a candidate's ceiling, not their most recent role, is
    the fairer comparison against a job's required level.
    """
    ranked = [
        (_rank(experience.seniority), experience.seniority)
        for experience in profile.experiences
        if experience.seniority and _rank(experience.seniority) is not None
    ]
    if not ranked:
        return SeniorityLevel.UNKNOWN
    return max(ranked, key=lambda pair: pair[0])[1]


def compare_seniority(required: SeniorityLevel, candidate: SeniorityLevel) -> SeniorityComparison:
    if candidate == SeniorityLevel.UNKNOWN:
        return SeniorityComparison.UNKNOWN
    required_rank, candidate_rank = _rank(required), _rank(candidate)
    if required_rank is None or candidate_rank is None:
        return SeniorityComparison.UNKNOWN
    if candidate_rank == required_rank:
        return SeniorityComparison.MEETS
    if candidate_rank > required_rank:
        return SeniorityComparison.EXCEEDS
    return SeniorityComparison.PARTIAL if candidate_rank == required_rank - 1 else SeniorityComparison.BELOW


_COMPARISON_TO_SIGNAL: dict[SeniorityComparison, MatchSignal] = {
    SeniorityComparison.MEETS: MatchSignal.EXACT_MATCH,
    SeniorityComparison.EXCEEDS: MatchSignal.EXACT_MATCH,
    SeniorityComparison.PARTIAL: MatchSignal.PARTIAL_MATCH,
    SeniorityComparison.BELOW: MatchSignal.NO_EVIDENCE,
    SeniorityComparison.UNKNOWN: MatchSignal.NO_EVIDENCE,
}


def evaluate_seniority_requirement(
    job: JobProfile, candidate: CandidateProfile
) -> RequirementEvaluation | None:
    """Returns None when the job states no discernible seniority - there
    is nothing to evaluate, and section 12 forbids inventing a gap out of
    an absent requirement.
    """
    required = job.seniority_normalized
    if required is None or required == SeniorityLevel.UNKNOWN:
        return None

    candidate_level = candidate_peak_seniority(candidate)
    comparison = compare_seniority(required, candidate_level)
    signal = _COMPARISON_TO_SIGNAL[comparison]
    status = (
        RequirementStatus.UNKNOWN
        if comparison == SeniorityComparison.UNKNOWN
        else RequirementStatus.MET
        if comparison in (SeniorityComparison.MEETS, SeniorityComparison.EXCEEDS)
        else RequirementStatus.PARTIALLY_MET
        if comparison == SeniorityComparison.PARTIAL
        else RequirementStatus.NOT_MET
    )
    candidate_label, required_label = candidate_level.value, required.value
    explanation = {
        SeniorityComparison.MEETS: (
            f"Candidate's demonstrated seniority ({candidate_label}) meets {required_label}."
        ),
        SeniorityComparison.EXCEEDS: (
            f"Candidate's demonstrated seniority ({candidate_label}) exceeds {required_label}."
        ),
        SeniorityComparison.PARTIAL: (
            f"Candidate's demonstrated seniority ({candidate_label}) is one level below {required_label}."
        ),
        SeniorityComparison.BELOW: (
            f"Candidate's demonstrated seniority ({candidate_label}) is below the required {required_label}."
        ),
        SeniorityComparison.UNKNOWN: f"Candidate's seniority could not be compared against {required_label}.",
    }[comparison]

    strength = strength_for_signal(signal)
    evidence = tuple(
        MatchEvidence(
            evidence=experience.evidence,
            source_type="EXPERIENCE",
            source_label=" at ".join(part for part in (experience.title, experience.company) if part)
            or None,
        )
        for experience in candidate.experiences
        if experience.seniority == candidate_level and experience.evidence is not None
    )
    return RequirementEvaluation(
        requirement_type=RequirementType.SENIORITY,
        priority=RequirementPriority.PREFERRED,
        raw_text=f"Seniority: {job.seniority or required.value}",
        status=status,
        match_signal=signal,
        match_strength=strength,
        score=SCORE_FOR_STRENGTH[strength],
        confidence=confidence_for_signal(signal),
        evidence=evidence,
        explanation=explanation,
    )
