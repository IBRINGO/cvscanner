"""Adversarial Truth Layer tests (Phase 5 section 72 - mandatory).

Each test in `TestAdversarialCases` reproduces one of the five exact
scenarios the brief lists verbatim: a job requirement that could tempt a
tailoring step to invent, upgrade, or inflate a candidate fact, and an
assertion that the claim validator catches it every time.
"""
from domain.cv.education_normalization import EducationLevel
from domain.cv.language_normalization import LanguageProficiency
from domain.skills.enrichment import TechnologyMentionScanner
from domain.skills.entities import Skill
from domain.skills.enums import SkillCategory
from domain.truth.claim_validation import (
    validate_certification_claims,
    validate_duration_claims,
    validate_education_claims,
    validate_generated_text,
    validate_language_claims,
    validate_technology_claims,
)
from domain.truth.enums import ClaimRejectionReason


def _skill(name: str, *aliases: str) -> Skill:
    return Skill(canonical_name=name, category=SkillCategory.TOOL, aliases=aliases)


_SCANNER = TechnologyMentionScanner(
    [
        _skill("Docker"),
        _skill("Kubernetes"),
        _skill("Python"),
        _skill("Django"),
        _skill("PostgreSQL", "Postgres"),
    ]
)


class TestAdversarialCases:
    """Verbatim section 72 scenarios."""

    def test_kubernetes_is_never_claimed_from_docker_alone(self):
        result = validate_technology_claims(
            original_text="Managed containerized deployments with Docker.",
            proposed_text="Managed Kubernetes clusters.",
            scanner=_SCANNER,
            known_skill_names=frozenset({"Docker"}),
        )
        assert len(result) == 1
        assert result[0].reason == ClaimRejectionReason.UNSUPPORTED_TECHNOLOGY

    def test_aws_certification_is_never_claimed_from_aws_skill_alone(self):
        result = validate_certification_claims(
            original_text="Worked extensively with AWS.",
            proposed_text="AWS Certified Solutions Architect with hands-on cloud experience.",
        )
        assert len(result) == 1
        assert result[0].reason == ClaimRejectionReason.UNSUPPORTED_CERTIFICATION

    def test_five_years_is_never_claimed_from_two_verified_years(self):
        result = validate_duration_claims(
            original_text="Python experience from 2024 to 2026.",
            proposed_text="5 years of professional Python experience.",
            verified_years=2.0,
        )
        assert len(result) == 1
        assert result[0].reason == ClaimRejectionReason.DURATION_INFLATION

    def test_native_english_is_never_claimed_from_b2_intermediate(self):
        result = validate_language_claims(
            proposed_text="Native English speaker.",
            verified_proficiency=LanguageProficiency.UPPER_INTERMEDIATE,
        )
        assert len(result) == 1
        assert result[0].reason == ClaimRejectionReason.LANGUAGE_PROFICIENCY_UPGRADE

    def test_masters_degree_is_never_claimed_from_a_bachelors(self):
        result = validate_education_claims(
            proposed_text="Master's degree in Computer Science.",
            highest_verified_level=EducationLevel.BACHELOR,
        )
        assert len(result) == 1
        assert result[0].reason == ClaimRejectionReason.EDUCATION_UPGRADE


class TestTechnologyClaims:
    def test_a_technology_already_in_the_original_text_is_never_flagged(self):
        result = validate_technology_claims(
            original_text="Built APIs with Django and PostgreSQL.",
            proposed_text="Built REST APIs with Django and PostgreSQL.",
            scanner=_SCANNER,
            known_skill_names=frozenset({"Django", "PostgreSQL"}),
        )
        assert result == ()

    def test_a_technology_the_candidate_genuinely_knows_elsewhere_is_allowed(self):
        result = validate_technology_claims(
            original_text="Built backend services.",
            proposed_text="Built backend services using Python.",
            scanner=_SCANNER,
            known_skill_names=frozenset({"Python"}),
        )
        assert result == ()


class TestCertificationClaims:
    def test_no_new_certification_wording_passes(self):
        result = validate_certification_claims(
            original_text="Worked with AWS.", proposed_text="Extensive AWS cloud experience."
        )
        assert result == ()

    def test_certification_wording_already_present_is_not_re_flagged(self):
        result = validate_certification_claims(
            original_text="AWS Certified Developer.",
            proposed_text="Holds AWS Certified Developer certification.",
        )
        assert result == ()


class TestDurationClaims:
    def test_no_duration_figure_in_proposal_passes(self):
        result = validate_duration_claims(
            original_text="Software engineer.", proposed_text="Backend software engineer.", verified_years=3.0
        )
        assert result == ()

    def test_a_duration_within_tolerance_passes(self):
        result = validate_duration_claims(
            original_text="", proposed_text="3 years of experience.", verified_years=3.2
        )
        assert result == ()

    def test_new_duration_with_no_verified_total_is_rejected_conservatively(self):
        result = validate_duration_claims(
            original_text="Backend engineer.",
            proposed_text="10 years as a backend engineer.",
            verified_years=None,
        )
        assert len(result) == 1
        assert result[0].reason == ClaimRejectionReason.DURATION_INFLATION


class TestEducationClaims:
    def test_matching_level_passes(self):
        result = validate_education_claims(
            proposed_text="Bachelor of Science in Computer Science.",
            highest_verified_level=EducationLevel.BACHELOR,
        )
        assert result == ()

    def test_no_education_wording_passes(self):
        result = validate_education_claims(
            proposed_text="Led a team of five engineers.", highest_verified_level=EducationLevel.HIGH_SCHOOL
        )
        assert result == ()


class TestLanguageClaims:
    def test_matching_or_lower_proficiency_passes(self):
        result = validate_language_claims(
            proposed_text="Intermediate English.", verified_proficiency=LanguageProficiency.UPPER_INTERMEDIATE
        )
        assert result == ()


class TestValidateGeneratedTextComposition:
    def test_multiple_violations_are_all_reported(self):
        result = validate_generated_text(
            original_text="Worked with Docker.",
            proposed_text="Kubernetes expert, AWS Certified Solutions Architect, 10 years experience.",
            scanner=_SCANNER,
            known_skill_names=frozenset({"Docker"}),
            verified_years=2.0,
        )
        assert not result.is_valid
        reasons = {v.reason for v in result.violations}
        assert ClaimRejectionReason.UNSUPPORTED_TECHNOLOGY in reasons
        assert ClaimRejectionReason.UNSUPPORTED_CERTIFICATION in reasons
        assert ClaimRejectionReason.DURATION_INFLATION in reasons

    def test_a_fully_safe_rewrite_produces_no_violations(self):
        result = validate_generated_text(
            original_text="Worked with Docker to containerize services.",
            proposed_text="Used Docker to containerize and deploy backend services.",
            scanner=_SCANNER,
            known_skill_names=frozenset({"Docker"}),
        )
        assert result.is_valid
