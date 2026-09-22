from datetime import date

from domain.cv.entities import Experience
from domain.job.entities import JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.matching.entities import RequirementEvaluation
from domain.matching.enums import MatchSignal, RequirementStatus
from domain.matching.experience_matching import (
    compute_years_of_experience,
    evaluate_experience_requirement,
)

REFERENCE = date(2026, 1, 1)


def _experience(start: str, end: str | None, technologies: tuple[str, ...] = ()) -> Experience:
    return Experience(
        title="Engineer",
        company="Acme",
        start_date_raw=start,
        end_date_raw=end,
        description=None,
        technologies=technologies,
    )


def _requirement(
    raw_text: str, minimum_years: int | None, normalized_value: str | None = None
) -> JobRequirement:
    return JobRequirement(
        requirement_type=RequirementType.EXPERIENCE,
        importance=RequirementImportance.REQUIRED,
        raw_text=raw_text,
        minimum_years=minimum_years,
        normalized_value=normalized_value,
    )


class TestComputeYearsOfExperience:
    def test_single_experience(self):
        result = compute_years_of_experience((_experience("2020", "2023"),), reference_date=REFERENCE)
        assert result.total_years == 3.0

    def test_present_uses_reference_date(self):
        result = compute_years_of_experience((_experience("2020", "Present"),), reference_date=REFERENCE)
        assert result.total_years == 6.0

    def test_overlapping_experiences_are_not_double_counted(self):
        experiences = (
            _experience("2018", "2022"),
            _experience("2020", "2023"),
        )
        result = compute_years_of_experience(experiences, reference_date=REFERENCE)
        assert result.total_years == 5.0  # union of 2018-2023, not 4+3=7

    def test_non_overlapping_experiences_are_summed(self):
        experiences = (
            _experience("2015", "2017"),
            _experience("2020", "2022"),
        )
        result = compute_years_of_experience(experiences, reference_date=REFERENCE)
        assert result.total_years == 4.0

    def test_filters_by_technology(self):
        experiences = (
            _experience("2020", "2023", technologies=("Python",)),
            _experience("2018", "2020", technologies=("Java",)),
        )
        result = compute_years_of_experience(experiences, technology="Python", reference_date=REFERENCE)
        assert result.total_years == 3.0

    def test_unparseable_dates_return_none_rather_than_a_guess(self):
        experiences = (_experience("a long time ago", None),)
        result = compute_years_of_experience(experiences, reference_date=REFERENCE)
        assert result.total_years is None


class TestEvaluateExperienceRequirement:
    def test_meets_requirement(self):
        requirement = _requirement("5 years of Python", 5, "Python")
        experiences = (_experience("2018", "2023", technologies=("Python",)),)

        evaluation = evaluate_experience_requirement(requirement, experiences, reference_date=REFERENCE)

        assert isinstance(evaluation, RequirementEvaluation)
        assert evaluation.match_signal == MatchSignal.EXACT_MATCH
        assert evaluation.status == RequirementStatus.MET

    def test_partially_meets_requirement(self):
        requirement = _requirement("5 years of Python", 5, "Python")
        experiences = (_experience("2022", "2023", technologies=("Python",)),)

        evaluation = evaluate_experience_requirement(requirement, experiences, reference_date=REFERENCE)

        assert evaluation.match_signal == MatchSignal.PARTIAL_MATCH
        assert evaluation.status == RequirementStatus.PARTIALLY_MET

    def test_no_matching_technology_is_no_evidence(self):
        requirement = _requirement("5 years of Python", 5, "Python")
        experiences = (_experience("2018", "2023", technologies=("Java",)),)

        evaluation = evaluate_experience_requirement(requirement, experiences, reference_date=REFERENCE)

        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE
        assert evaluation.status == RequirementStatus.NOT_MET

    def test_unparseable_dates_report_unknown_not_a_fabricated_number(self):
        requirement = _requirement("5 years of Python", 5, "Python")
        experiences = (_experience("a long time ago", None, technologies=("Python",)),)

        evaluation = evaluate_experience_requirement(requirement, experiences, reference_date=REFERENCE)

        assert evaluation.status == RequirementStatus.UNKNOWN
        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE

    def test_ambiguous_requirement_without_a_year_count_still_reports_relevant_experience(self):
        requirement = _requirement("Significant experience with Django", None, "Django")
        experiences = (_experience("2020", "2023", technologies=("Django",)),)

        evaluation = evaluate_experience_requirement(requirement, experiences, reference_date=REFERENCE)

        assert evaluation.status == RequirementStatus.PARTIALLY_MET
