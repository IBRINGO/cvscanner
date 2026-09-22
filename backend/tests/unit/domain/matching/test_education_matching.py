from domain.cv.education_normalization import EducationLevel
from domain.cv.entities import CandidateProfile, Contact, Education
from domain.job.entities import JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.matching.education_matching import (
    candidate_highest_education,
    compare_education,
    evaluate_education_requirement,
)
from domain.matching.enums import EducationComparison, RequirementStatus


def _profile(*levels: EducationLevel) -> CandidateProfile:
    education = tuple(
        Education(
            institution="U",
            degree=None,
            field_of_study=None,
            start_date_raw=None,
            end_date_raw=None,
            degree_level=level,
        )
        for level in levels
    )
    return CandidateProfile(full_name=None, contact=Contact(), summary=None, education=education)


def _requirement(normalized_value: str | None) -> JobRequirement:
    return JobRequirement(
        requirement_type=RequirementType.EDUCATION,
        importance=RequirementImportance.REQUIRED,
        raw_text="Bachelor's degree required",
        normalized_value=normalized_value,
    )


class TestCandidateHighestEducation:
    def test_returns_highest_level(self):
        profile = _profile(EducationLevel.BACHELOR, EducationLevel.MASTER)
        level, _ = candidate_highest_education(profile)
        assert level == EducationLevel.MASTER

    def test_unknown_when_nothing_evidenced(self):
        profile = _profile()
        level, entry = candidate_highest_education(profile)
        assert level == EducationLevel.UNKNOWN
        assert entry is None


class TestCompareEducation:
    def test_meets(self):
        result = compare_education(EducationLevel.BACHELOR, EducationLevel.BACHELOR)
        assert result == EducationComparison.MEETS

    def test_exceeds(self):
        result = compare_education(EducationLevel.BACHELOR, EducationLevel.MASTER)
        assert result == EducationComparison.EXCEEDS

    def test_below(self):
        result = compare_education(EducationLevel.MASTER, EducationLevel.BACHELOR)
        assert result == EducationComparison.BELOW

    def test_professional_certificate_is_not_inferred_as_a_degree(self):
        # Excluded from the academic ladder entirely - never counted as
        # meeting or exceeding a degree requirement.
        result = compare_education(EducationLevel.BACHELOR, EducationLevel.PROFESSIONAL_CERTIFICATE)
        assert result == EducationComparison.UNKNOWN


class TestEvaluateEducationRequirement:
    def test_meets_requirement(self):
        requirement = _requirement("BACHELOR")
        profile = _profile(EducationLevel.BACHELOR)
        evaluation = evaluate_education_requirement(requirement, profile)
        assert evaluation.status == RequirementStatus.MET

    def test_no_education_evidenced_is_unknown_not_fabricated(self):
        requirement = _requirement("BACHELOR")
        profile = _profile()
        evaluation = evaluate_education_requirement(requirement, profile)
        assert evaluation.status == RequirementStatus.UNKNOWN
