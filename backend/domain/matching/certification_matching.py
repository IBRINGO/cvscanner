"""Certification requirement matching (section 15 of the Phase 4 brief).

Deliberately consults ONLY `CandidateProfile.certifications` - never
skills. Holding a skill in the same technology area (e.g. "AWS" as a
skill) is explicitly NOT evidence of holding a named certification (e.g.
"AWS Certified Solutions Architect"); the brief calls this out directly
("AWS skill != AWS certification").
"""
from domain.cv.entities import CandidateProfile, Certification
from domain.job.entities import JobRequirement
from domain.matching.entities import MatchEvidence, RequirementEvaluation
from domain.matching.enums import MatchSignal, RequirementStatus
from domain.matching.priority import priority_from_importance
from domain.matching.strength import SCORE_FOR_STRENGTH, confidence_for_signal, strength_for_signal


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def find_matching_certification(
    requirement_text: str, certifications: tuple[Certification, ...]
) -> tuple[Certification, MatchSignal] | None:
    needle = _normalize(requirement_text)
    for certification in certifications:
        name = _normalize(certification.name)
        if name == needle:
            return certification, MatchSignal.EXACT_MATCH
    for certification in certifications:
        name = _normalize(certification.name)
        if needle in name or name in needle:
            return certification, MatchSignal.PARTIAL_MATCH
    return None


def evaluate_certification_requirement(
    requirement: JobRequirement, profile: CandidateProfile
) -> RequirementEvaluation:
    priority = priority_from_importance(requirement.importance)
    found = find_matching_certification(requirement.raw_text, profile.certifications)

    if found is None:
        return _evaluation(
            requirement,
            priority,
            signal=MatchSignal.NO_EVIDENCE,
            status=RequirementStatus.NOT_MET,
            certification=None,
            explanation=(
                f"No certification matching '{requirement.raw_text}' was found. "
                "A related skill on the CV is not treated as certification evidence."
            ),
        )

    certification, signal = found
    status = RequirementStatus.MET if signal == MatchSignal.EXACT_MATCH else RequirementStatus.PARTIALLY_MET
    explanation = (
        f"Candidate lists '{certification.name}'"
        + (f" ({certification.issuer})" if certification.issuer else "")
        + "."
    )
    return _evaluation(
        requirement,
        priority,
        signal=signal,
        status=status,
        certification=certification,
        explanation=explanation,
    )


def _evaluation(
    requirement: JobRequirement,
    priority,
    *,
    signal: MatchSignal,
    status: RequirementStatus,
    certification: Certification | None,
    explanation: str,
) -> RequirementEvaluation:
    strength = strength_for_signal(signal)
    evidence = ()
    if certification is not None and certification.evidence is not None:
        evidence = (MatchEvidence(evidence=certification.evidence, source_type="CERTIFICATION"),)
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
