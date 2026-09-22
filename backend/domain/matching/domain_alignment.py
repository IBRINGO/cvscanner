"""Domain/industry-landscape alignment (section 17 of the Phase 4
brief). Uses Phase 3's `SkillDomain` grouping - never a substitute for a
missing mandatory requirement, only supporting evidence (hence the small
dimension weight in domain/matching/weights.py).
"""
from collections import Counter

from domain.cv.entities import CandidateProfile
from domain.job.entities import JobProfile
from domain.job.enums import RequirementType
from domain.matching.entities import RequirementEvaluation
from domain.matching.enums import MatchSignal, RequirementPriority, RequirementStatus
from domain.matching.strength import SCORE_FOR_STRENGTH, confidence_for_signal, strength_for_signal
from domain.skills.enums import skill_domain_for_category


def required_domains(job: JobProfile) -> set[str]:
    domains: set[str] = set()
    for requirement in job.requirements:
        if requirement.requirement_type in (RequirementType.REQUIRED_SKILL, RequirementType.PREFERRED_SKILL):
            if requirement.skill is not None:
                domains.add(skill_domain_for_category(requirement.skill.category).value)
    return domains


def candidate_domain_distribution(candidate: CandidateProfile) -> Counter:
    counts: Counter = Counter()
    for mention in candidate.skills:
        if mention.skill is not None:
            counts[skill_domain_for_category(mention.skill.category).value] += 1
    return counts


def evaluate_domain_alignment(job: JobProfile, candidate: CandidateProfile) -> RequirementEvaluation | None:
    """Returns None when the job's requirements don't resolve to any
    known skill domain - there is nothing meaningful to compare.
    """
    job_domains = required_domains(job)
    if not job_domains:
        return None

    candidate_domains = candidate_domain_distribution(candidate)
    overlapping = job_domains & set(candidate_domains)

    if overlapping:
        dominant = max(overlapping, key=lambda domain: candidate_domains[domain])
        signal = MatchSignal.EXACT_MATCH
        domain_label = dominant.replace("_", " ").title()
        explanation = f"Candidate's skill landscape aligns with the {domain_label} domain this role requires."
    else:
        signal = MatchSignal.NO_EVIDENCE
        explanation = "Candidate's demonstrated skills do not align with this role's primary domain."

    strength = strength_for_signal(signal)
    status = RequirementStatus.MET if signal == MatchSignal.EXACT_MATCH else RequirementStatus.NOT_MET
    return RequirementEvaluation(
        requirement_type=RequirementType.OTHER,
        priority=RequirementPriority.OPTIONAL,
        raw_text="Domain alignment",
        status=status,
        match_signal=signal,
        match_strength=strength,
        score=SCORE_FOR_STRENGTH[strength],
        confidence=confidence_for_signal(signal),
        evidence=(),
        explanation=explanation,
    )
