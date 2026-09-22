from domain.cv.entities import CandidateProfile, CandidateSkillMention, Certification, Contact
from domain.job.entities import JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.matching.certification_matching import evaluate_certification_requirement
from domain.matching.enums import MatchSignal, RequirementStatus
from domain.skills.entities import Skill
from domain.skills.enums import SkillCategory


def _requirement(text: str) -> JobRequirement:
    return JobRequirement(
        requirement_type=RequirementType.CERTIFICATION,
        importance=RequirementImportance.PREFERRED,
        raw_text=text,
    )


class TestEvaluateCertificationRequirement:
    def test_exact_certification_match(self):
        requirement = _requirement("AWS Certified Solutions Architect")
        profile = CandidateProfile(
            full_name=None,
            contact=Contact(),
            summary=None,
            certifications=(
                Certification(name="AWS Certified Solutions Architect", issuer="Amazon", date_raw="2021"),
            ),
        )

        evaluation = evaluate_certification_requirement(requirement, profile)

        assert evaluation.match_signal == MatchSignal.EXACT_MATCH
        assert evaluation.status == RequirementStatus.MET

    def test_skill_alone_is_never_treated_as_certification_evidence(self):
        requirement = _requirement("AWS Certified Solutions Architect")
        aws_skill = Skill("Amazon Web Services", SkillCategory.CLOUD)
        profile = CandidateProfile(
            full_name=None,
            contact=Contact(),
            summary=None,
            skills=(CandidateSkillMention(raw_text="AWS", skill=aws_skill),),
            certifications=(),
        )

        evaluation = evaluate_certification_requirement(requirement, profile)

        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE
        assert evaluation.status == RequirementStatus.NOT_MET

    def test_no_certification_at_all(self):
        requirement = _requirement("Scrum Master")
        profile = CandidateProfile(full_name=None, contact=Contact(), summary=None)

        evaluation = evaluate_certification_requirement(requirement, profile)

        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE
