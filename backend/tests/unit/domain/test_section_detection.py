from domain.cv.policies import detect_sections, normalize_section_heading
from domain.documents.entities import LineRecord, ParsedDocument, ParsedPage
from domain.documents.enums import DocumentLanguage, SectionType


class TestNormalizeSectionHeading:
    def test_exact_alias_match(self):
        assert normalize_section_heading("Skills") == SectionType.SKILLS

    def test_known_alias_variant(self):
        assert normalize_section_heading("Professional Experience") == SectionType.EXPERIENCE
        assert normalize_section_heading("Work Experience") == SectionType.EXPERIENCE
        assert normalize_section_heading("Employment History") == SectionType.EXPERIENCE

    def test_recognizes_a_bilingual_taxonomy_entry_added_by_the_overhaul(self):
        # "Hobbies" used to fall back to OTHER (the pre-overhaul taxonomy
        # had no HOBBIES entry at all) - the document-intelligence
        # overhaul added it as a first-class canonical section (see
        # domain/documents/enums.py::SectionType), so this is an
        # intentional behavior change, not a regression.
        assert normalize_section_heading("Hobbies") == SectionType.HOBBIES
        assert normalize_section_heading("Loisirs") == SectionType.HOBBIES

    def test_unrecognized_heading_falls_back_to_other(self):
        assert normalize_section_heading("Xyzzy Plugh") == SectionType.OTHER

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

    def test_splits_a_french_cv_by_its_french_headings(self):
        text = (
            "PROFIL\n"
            "Ingenieure back-end avec 6 ans d'experience.\n\n"
            "EXPERIENCE PROFESSIONNELLE\n"
            "Ingenieure chez Meridian Analytics\n"
            "Janvier 2020 - Present\n\n"
            "FORMATION\n"
            "Master en informatique, MIT\n\n"
            "COMPETENCES\n"
            "Python, Django"
        )
        sections = detect_sections(self._parsed(text))
        types = [s.section_type for s in sections]
        assert types == [
            SectionType.SUMMARY,
            SectionType.EXPERIENCE,
            SectionType.EDUCATION,
            SectionType.SKILLS,
        ]

    def test_attaches_the_detected_document_language_to_every_section(self):
        text = (
            "SUMMARY\nAn engineer with experience building systems for the team.\n\n"
            "SKILLS\nPython, Django"
        )
        sections = detect_sections(self._parsed(text))
        assert all(s.language == DocumentLanguage.EN for s in sections)

    def test_accepts_an_explicit_language_without_recomputing_it(self):
        text = "SUMMARY\nA bio.\n\nSKILLS\nPython"
        sections = detect_sections(self._parsed(text), language=DocumentLanguage.FR)
        assert all(s.language == DocumentLanguage.FR for s in sections)

    def test_uses_line_records_in_column_order_when_the_parser_provided_them(self):
        # Simulates what a layout-aware PDF parser hands over for a
        # two-column page: left column's lines fully before the right
        # column's, each tagged with its own column_index - detect_sections
        # must not need to re-sort anything, just walk the list.
        records = [
            LineRecord(page_number=1, text="SKILLS", column_index=0),
            LineRecord(page_number=1, text="Python", column_index=0),
            LineRecord(page_number=1, text="", column_index=0),
            LineRecord(page_number=1, text="EXPERIENCE", column_index=1),
            LineRecord(page_number=1, text="Engineer at Acme", column_index=1),
        ]
        parsed = ParsedDocument(raw_text="", pages=[], line_records=records)
        sections = detect_sections(parsed)
        assert [s.section_type for s in sections] == [SectionType.SKILLS, SectionType.EXPERIENCE]
        assert sections[0].column_index == 0
        assert sections[1].column_index == 1

    def test_a_larger_bold_line_is_scored_as_a_heading_even_without_an_alias_hit(self):
        # "Awards & Recognition" isn't a literal alias, but a much-larger
        # bold line short enough to be a heading should still score above
        # threshold via the font-size/bold signals, and normalize via the
        # substring fallback ("awards" is in the ACHIEVEMENTS aliases).
        records = [
            LineRecord(page_number=1, text="Some body copy at normal size.", font_size=10, is_bold=False),
            LineRecord(page_number=1, text="Awards Recognition", font_size=16, is_bold=True),
            LineRecord(page_number=1, text="Employee of the year, 2022.", font_size=10, is_bold=False),
        ]
        parsed = ParsedDocument(raw_text="", pages=[], line_records=records)
        sections = detect_sections(parsed)
        assert any(s.section_type == SectionType.ACHIEVEMENTS for s in sections)

    def test_a_docx_heading_style_line_is_always_treated_as_a_heading(self):
        records = [
            LineRecord(page_number=None, text="Something Unusual", is_heading_style=True),
            LineRecord(page_number=None, text="Body copy under it."),
        ]
        parsed = ParsedDocument(raw_text="", pages=[], line_records=records)
        sections = detect_sections(parsed)
        assert sections[0].heading_text == "Something Unusual"
        assert sections[0].confidence >= 0.9
