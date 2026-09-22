from domain.cv.entities import CandidateProfile, Contact, Experience
from domain.cv.seniority import SeniorityLevel
from domain.job.entities import JobProfile
from domain.matching.enums import SeniorityComparison
from domain.matching.seniority_matching import (
    candidate_peak_seniority,
    compare_seniority,
    evaluate_seniority_requirement,
)


def _profile(*seniorities: SeniorityLevel) -> CandidateProfile:
    experiences = tuple(
        Experience(
            title="Engineer",
            company="Acme",
            start_date_raw=None,
            end_date_raw=None,
            description=None,
            seniority=level,
        )
        for level in seniorities
    )
    return CandidateProfile(full_name=None, contact=Contact(), summary=None, experiences=experiences)


def _job(seniority_normalized: SeniorityLevel | None) -> JobProfile:
    return JobProfile(
        title=None, company=None, location=None, employment_type=None, seniority=None, summary=None,
        seniority_normalized=seniority_normalized,
    )


class TestCandidatePeakSeniority:
    def test_returns_highest_level(self):
        profile = _profile(SeniorityLevel.MID, SeniorityLevel.SENIOR, SeniorityLevel.JUNIOR)
        assert candidate_peak_seniority(profile) == SeniorityLevel.SENIOR

    def test_unknown_when_nothing_evidenced(self):
        profile = _profile(SeniorityLevel.UNKNOWN)
        assert candidate_peak_seniority(profile) == SeniorityLevel.UNKNOWN


class TestCompareSeniority:
    def test_meets(self):
        assert compare_seniority(SeniorityLevel.SENIOR, SeniorityLevel.SENIOR) == SeniorityComparison.MEETS

    def test_exceeds(self):
        assert compare_seniority(SeniorityLevel.MID, SeniorityLevel.SENIOR) == SeniorityComparison.EXCEEDS

    def test_below(self):
        assert compare_seniority(SeniorityLevel.SENIOR, SeniorityLevel.JUNIOR) == SeniorityComparison.BELOW

    def test_unknown_candidate_is_unknown_not_below(self):
        assert compare_seniority(SeniorityLevel.SENIOR, SeniorityLevel.UNKNOWN) == SeniorityComparison.UNKNOWN


class TestEvaluateSeniorityRequirement:
    def test_no_requirement_returns_none(self):
        job = _job(None)
        profile = _profile(SeniorityLevel.SENIOR)
        assert evaluate_seniority_requirement(job, profile) is None

    def test_meets_requirement(self):
        job = _job(SeniorityLevel.SENIOR)
        profile = _profile(SeniorityLevel.SENIOR)
        evaluation = evaluate_seniority_requirement(job, profile)
        assert evaluation.status.value == "MET"

    def test_unknown_is_never_treated_as_failure(self):
        job = _job(SeniorityLevel.SENIOR)
        profile = _profile(SeniorityLevel.UNKNOWN)
        evaluation = evaluate_seniority_requirement(job, profile)
        assert evaluation.status.value == "UNKNOWN"
        assert evaluation.status.value != "NOT_MET"
