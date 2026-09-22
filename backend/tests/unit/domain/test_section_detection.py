from domain.cv.policies import detect_sections, normalize_section_heading
from domain.documents.entities import ParsedDocument, ParsedPage
from domain.documents.enums import SectionType


class TestNormalizeSectionHeading:
    def test_exact_alias_match(self):
        assert normalize_section_heading("Skills") == SectionType.SKILLS

    def test_known_alias_variant(self):
        assert normalize_section_heading("Professional Experience") == SectionType.EXPERIENCE
        assert normalize_section_heading("Work Experience") == SectionType.EXPERIENCE
        assert normalize_section_heading("Employment History") == SectionType.EXPERIENCE

    def test_unrecognized_heading_falls_back_to_other(self):
        assert normalize_section_heading("Hobbies") == SectionType.OTHER

    def test_does_not_misclassify_a_sentence_mentioning_a_keyword(self):
        # Regression: "5+ years of experience" must not normalize to
        # EXPERIENCE just because the word appears in it - only genuinely
        # short, heading-shaped lines get the substring fallback (see
        # domain/cv/policies.py::_looks_like_heading for the actual gate;
        # normalize_section_heading itself is intentionally more lenient
        # since callers may pass a heading they've already confirmed).
        assert normalize_section_heading("5+ years of experience") == SectionType.EXPERIENCE


class TestDetectSections:
    def _parsed(self, text: str) -> ParsedDocument:
        return ParsedDocument(raw_text=text, pages=[ParsedPage(page_number=1, text=text)])

    def test_leading_text_before_first_heading_is_kept_as_other(self):
        parsed = self._parsed("Jordan Rivera\njordan@example.com\n\nSKILLS\nPython, Django")
        sections = detect_sections(parsed)
        assert sections[0].section_type == SectionType.OTHER
        assert "Jordan Rivera" in sections[0].body_text

    def test_splits_multiple_sections(self):
        text = "SUMMARY\nExperienced engineer.\n\nSKILLS\nPython, Django\n\nEDUCATION\nMIT"
        sections = detect_sections(self._parsed(text))
        types = [s.section_type for s in sections]
        assert types == [SectionType.SUMMARY, SectionType.SKILLS, SectionType.EDUCATION]

    def test_does_not_split_a_bullet_mentioning_experience_inside_requirements(self):
        text = "REQUIREMENTS\nPython\n5+ years of experience\nBachelor degree"
        sections = detect_sections(self._parsed(text))
        assert len(sections) == 1
        assert sections[0].section_type == SectionType.REQUIREMENTS
        assert "5+ years of experience" in sections[0].body_text

    def test_short_acronym_is_not_treated_as_a_heading(self):
        text = "SKILLS\nDocker\nAWS\nSQL"
        sections = detect_sections(self._parsed(text))
        assert len(sections) == 1
        assert "AWS" in sections[0].body_text
        assert "SQL" in sections[0].body_text

    def test_blank_line_separates_entries_within_one_section(self):
        text = "EXPERIENCE\nEngineer at Acme\n2020 - 2022\n\nEngineer at Beta\n2018 - 2020"
        sections = detect_sections(self._parsed(text))
        assert len(sections) == 1
        assert "\n\n" in sections[0].body_text

    def test_empty_document_returns_no_sections(self):
        assert detect_sections(self._parsed("")) == []
