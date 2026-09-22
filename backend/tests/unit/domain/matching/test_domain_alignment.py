from domain.cv.entities import CandidateProfile, CandidateSkillMention, Contact
from domain.job.entities import JobProfile, JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.matching.domain_alignment import evaluate_domain_alignment
from domain.matching.enums import MatchSignal
from domain.skills.entities import Skill
from domain.skills.enums import SkillCategory


def _empty_job(**overrides) -> JobProfile:
    defaults = dict(
        title=None, company=None, location=None, employment_type=None, seniority=None, summary=None
    )
    defaults.update(overrides)
    return JobProfile(**defaults)


def _job(*skill_names: str) -> JobProfile:
    requirements = tuple(
        JobRequirement(
            requirement_type=RequirementType.REQUIRED_SKILL,
            importance=RequirementImportance.REQUIRED,
            raw_text=name,
            skill=Skill(name, SkillCategory.FRAMEWORK),
        )
        for name in skill_names
    )
    return _empty_job(requirements=requirements)


def _profile(*skill_names: str) -> CandidateProfile:
    mentions = tuple(
        CandidateSkillMention(raw_text=name, skill=Skill(name, SkillCategory.FRAMEWORK))
        for name in skill_names
    )
    return CandidateProfile(full_name=None, contact=Contact(), summary=None, skills=mentions)


class TestEvaluateDomainAlignment:
    def test_no_requirements_with_skills_returns_none(self):
        job = _empty_job()
        profile = _profile("Django")
        assert evaluate_domain_alignment(job, profile) is None

    def test_overlapping_domain_is_a_match(self):
        job = _job("Django")
        profile = _profile("React")  # both SOFTWARE_DEVELOPMENT domain

        evaluation = evaluate_domain_alignment(job, profile)

        assert evaluation.match_signal == MatchSignal.EXACT_MATCH

    def test_never_overrides_missing_mandatory_requirements(self):
        # Domain alignment produces a supporting evaluation only - it is
        # the caller's job (scoring.py) to keep this a small weight, but
        # at minimum this evaluation must be OPTIONAL priority.
        job = _job("Django")
        profile = _profile("React")
        evaluation = evaluate_domain_alignment(job, profile)
        assert evaluation.priority.value == "OPTIONAL"
