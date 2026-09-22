from domain.cv.policies import detect_sections
from domain.job.enums import RequirementImportance, RequirementType
from infrastructure.document_processing.extraction.job_extractor import RuleBasedJobExtractor
from infrastructure.document_processing.parsers.plain_text_parser import PlainTextParser


class TestRuleBasedJobExtractor:
    def _extract(self, fixture_bytes, skill_alias_index):
        parsed = PlainTextParser().parse(fixture_bytes("sample_job_offer.txt"), "sample_job_offer.txt")
        sections = detect_sections(parsed)
        return RuleBasedJobExtractor(skill_alias_index).extract(
            document_id="job-1", parsed=parsed, sections=sections
        )

    def test_extracts_title_and_labeled_fields(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        assert profile.title == "Senior Backend Engineer"
        assert profile.company == "Meridian Analytics"
        assert profile.location == "Remote"
        assert profile.employment_type == "Full-time"
        assert profile.seniority == "Senior"

    def test_extracts_responsibilities(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        assert "Design and maintain REST APIs" in profile.responsibilities
        assert len(profile.responsibilities) == 3

    def test_distinguishes_required_and_preferred_skills(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        required = [r for r in profile.requirements if r.importance == RequirementImportance.REQUIRED]
        preferred = [r for r in profile.requirements if r.importance == RequirementImportance.PREFERRED]

        required_skills = {r.skill.canonical_name for r in required if r.skill}
        preferred_skills = {r.skill.canonical_name for r in preferred if r.skill}

        assert {"Python", "Django", "PostgreSQL"} <= required_skills
        assert {"Docker", "Kubernetes", "Amazon Web Services"} <= preferred_skills

    def test_short_acronym_preferred_skill_not_lost_as_a_heading(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        aws_requirement = next(r for r in profile.requirements if r.raw_text == "AWS")
        assert aws_requirement.importance == RequirementImportance.PREFERRED
        assert aws_requirement.skill.canonical_name == "Amazon Web Services"

    def test_classifies_experience_and_education_requirements(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        types = {r.requirement_type for r in profile.requirements}
        assert RequirementType.EXPERIENCE in types
        assert RequirementType.EDUCATION in types

    def test_every_requirement_has_evidence(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        assert len(profile.requirements) == 8
        for requirement in profile.requirements:
            assert requirement.evidence is not None
            assert requirement.evidence.section.value == "REQUIREMENTS"

    def test_no_candidate_comparison_concept_is_present(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        # There must be nothing resembling a match/compatibility verdict
        # anywhere on the profile or its requirements (sections 24-25).
        assert not hasattr(profile, "match_score")
        for requirement in profile.requirements:
            assert not hasattr(requirement, "matched")
            assert not hasattr(requirement, "satisfied")


class TestRuleBasedJobExtractorEdgeCases:
    def test_job_with_no_explicit_skills_produces_no_skill_requirements(self, skill_alias_index):
        from domain.documents.entities import ParsedDocument

        text = "Office Assistant\n\nREQUIREMENTS\nMust be reliable and punctual"
        parsed = ParsedDocument(raw_text=text, pages=[])
        sections = detect_sections(parsed)

        profile, _ = RuleBasedJobExtractor(skill_alias_index).extract(
            document_id="job-2", parsed=parsed, sections=sections
        )

        skill_requirements = [r for r in profile.requirements if r.skill is not None]
        assert skill_requirements == []
