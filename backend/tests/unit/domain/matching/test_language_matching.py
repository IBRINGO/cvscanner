from domain.cv.entities import CandidateProfile, Contact, Language
from domain.cv.language_normalization import LanguageProficiency
from domain.job.entities import JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.matching.enums import MatchSignal, ProficiencyComparison, RequirementStatus
from domain.matching.language_matching import compare_proficiency, evaluate_language_requirement


def _profile(name: str, canonical: str, proficiency: LanguageProficiency | None) -> CandidateProfile:
    return CandidateProfile(
        full_name=None,
        contact=Contact(),
        summary=None,
        languages=(Language(name=name, canonical_name=canonical, proficiency_normalized=proficiency),),
    )


def _requirement(text: str) -> JobRequirement:
    return JobRequirement(
        requirement_type=RequirementType.LANGUAGE, importance=RequirementImportance.REQUIRED, raw_text=text
    )


class TestCompareProficiency:
    def test_absent_when_no_language(self):
        result = compare_proficiency(LanguageProficiency.UPPER_INTERMEDIATE, None)
        assert result == ProficiencyComparison.ABSENT

    def test_present_unknown_level(self):
        language = Language(name="English", canonical_name="English", proficiency_normalized=None)
        result = compare_proficiency(LanguageProficiency.UPPER_INTERMEDIATE, language)
        assert result == ProficiencyComparison.PRESENT_UNKNOWN_LEVEL


class TestEvaluateLanguageRequirement:
    def test_exact_proficiency_match(self):
        requirement = _requirement("English B2")
        profile = _profile("English", "English", LanguageProficiency.UPPER_INTERMEDIATE)

        evaluation = evaluate_language_requirement(requirement, profile)

        assert evaluation.match_signal == MatchSignal.EXACT_MATCH
        assert evaluation.status == RequirementStatus.MET

    def test_higher_proficiency_still_meets(self):
        requirement = _requirement("English B2")
        profile = _profile("English", "English", LanguageProficiency.NATIVE)

        evaluation = evaluate_language_requirement(requirement, profile)

        assert evaluation.status == RequirementStatus.MET

    def test_lower_proficiency_is_partial(self):
        requirement = _requirement("English C1")
        profile = _profile("English", "English", LanguageProficiency.INTERMEDIATE)

        evaluation = evaluate_language_requirement(requirement, profile)

        assert evaluation.status == RequirementStatus.PARTIALLY_MET
        assert evaluation.match_signal == MatchSignal.PARTIAL_MATCH

    def test_language_absent_entirely(self):
        requirement = _requirement("French C1")
        profile = _profile("English", "English", LanguageProficiency.NATIVE)

        evaluation = evaluate_language_requirement(requirement, profile)

        assert evaluation.match_signal == MatchSignal.NO_EVIDENCE
        assert evaluation.status == RequirementStatus.NOT_MET
