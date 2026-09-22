from domain.cv.policies import detect_sections
from infrastructure.document_processing.extraction.candidate_extractor import (
    RuleBasedCandidateExtractor,
)
from infrastructure.document_processing.parsers.pdf_parser import PDFParser


class TestRuleBasedCandidateExtractorOnPDF:
    def _extract(self, fixture_bytes, skill_alias_index):
        parsed = PDFParser().parse(fixture_bytes("sample_cv.pdf"), "sample_cv.pdf")
        sections = detect_sections(parsed)
        extractor = RuleBasedCandidateExtractor(skill_alias_index)
        return extractor.extract(document_id="doc-1", parsed=parsed, sections=sections)

    def test_extracts_identity_and_contact(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        assert profile.full_name == "Jordan Rivera"
        assert profile.contact.email == "jordan.rivera@example.com"
        assert profile.contact.phone == "+1 415 555 0199"
        assert profile.contact.location == "San Francisco, CA"

    def test_extracts_both_experience_entries(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        assert len(profile.experiences) == 2
        first = profile.experiences[0]
        assert first.title == "Senior Backend Engineer"
        assert first.company == "Meridian Analytics"
        assert first.start_date_raw == "January 2020"
        assert first.end_date_raw == "Present"
        assert "Reduced API latency by 40 percent" in first.achievements
        assert "Python" in first.technologies

    def test_every_experience_has_evidence(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        for experience in profile.experiences:
            assert experience.evidence is not None
            assert experience.evidence.page_number == 1
            assert 0.0 <= experience.evidence.confidence <= 1.0

    def test_extracts_education(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        assert len(profile.education) == 1
        assert profile.education[0].institution == "University of Washington"
        assert profile.education[0].degree == "BSc Computer Science"

    def test_extracts_single_certification_not_split_on_commas(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        assert len(profile.certifications) == 1
        cert = profile.certifications[0]
        assert cert.name == "AWS Certified Solutions Architect"
        assert cert.issuer == "Amazon"
        assert cert.date_raw == "2021"

    def test_extracts_languages(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        languages = {lang.name: lang.proficiency for lang in profile.languages}
        assert languages == {"English": "Native", "Spanish": "Conversational"}

    def test_normalizes_known_skills_and_keeps_evidence(self, fixture_bytes, skill_alias_index):
        profile, _ = self._extract(fixture_bytes, skill_alias_index)

        skill_names = {mention.raw_text: mention.skill for mention in profile.skills}
        assert skill_names["Python"].canonical_name == "Python"
        assert skill_names["Django"].canonical_name == "Django"
        for mention in profile.skills:
            assert mention.evidence is not None
            assert mention.evidence.section.value == "SKILLS"

    def test_document_level_evidence_includes_name_and_contact(self, fixture_bytes, skill_alias_index):
        _, document_level_evidence = self._extract(fixture_bytes, skill_alias_index)

        fields = {e.metadata.get("field") for e in document_level_evidence}
        assert {"full_name", "email", "phone", "location"} <= fields


class TestRuleBasedCandidateExtractorEdgeCases:
    def test_cv_with_no_experience_section_produces_empty_experiences(self, skill_alias_index):
        from domain.documents.entities import ParsedDocument, ParsedPage

        text = "Alex Doe\nalex@example.com\n\nSKILLS\nPython"
        parsed = ParsedDocument(raw_text=text, pages=[ParsedPage(1, text)])
        sections = detect_sections(parsed)

        profile, _ = RuleBasedCandidateExtractor(skill_alias_index).extract(
            document_id="doc-2", parsed=parsed, sections=sections
        )

        assert profile.experiences == ()
        assert profile.full_name == "Alex Doe"

    def test_cv_with_no_skills_section_produces_empty_skills(self, skill_alias_index):
        from domain.documents.entities import ParsedDocument, ParsedPage

        text = "Alex Doe\nalex@example.com\n\nSUMMARY\nA short bio."
        parsed = ParsedDocument(raw_text=text, pages=[ParsedPage(1, text)])
        sections = detect_sections(parsed)

        profile, _ = RuleBasedCandidateExtractor(skill_alias_index).extract(
            document_id="doc-3", parsed=parsed, sections=sections
        )

        assert profile.skills == ()

    def test_unrecognized_skill_kept_as_raw_text_not_dropped(self, skill_alias_index):
        from domain.documents.entities import ParsedDocument, ParsedPage

        text = "Alex Doe\n\nSKILLS\nSomeInternalTool, Python"
        parsed = ParsedDocument(raw_text=text, pages=[ParsedPage(1, text)])
        sections = detect_sections(parsed)

        profile, _ = RuleBasedCandidateExtractor(skill_alias_index).extract(
            document_id="doc-4", parsed=parsed, sections=sections
        )

        raw_texts = [mention.raw_text for mention in profile.skills]
        matched = {mention.raw_text: mention.skill for mention in profile.skills}
        assert "SomeInternalTool" in raw_texts
        assert matched["SomeInternalTool"] is None
        assert matched["Python"].canonical_name == "Python"
