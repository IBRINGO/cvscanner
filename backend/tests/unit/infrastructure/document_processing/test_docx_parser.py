import pytest

from domain.documents.exceptions import DocumentParsingError
from infrastructure.document_processing.parsers.docx_parser import DOCXParser


class TestDOCXParser:
    def test_extracts_text_with_no_page_numbers(self, fixture_bytes):
        parsed = DOCXParser().parse(fixture_bytes("sample_cv.docx"), "sample_cv.docx")

        assert "Jordan Rivera" in parsed.raw_text
        assert parsed.pages == []
        assert parsed.page_count is None
        assert all(block.page_number is None for block in parsed.blocks)

    def test_preserves_blank_line_gap_between_entries(self, fixture_bytes):
        parsed = DOCXParser().parse(fixture_bytes("sample_cv.docx"), "sample_cv.docx")

        experience_section = parsed.raw_text.split("EXPERIENCE", 1)[1]
        assert "\n\n" in experience_section.split("EDUCATION")[0]

    def test_corrupted_docx_raises_parsing_error(self, fixture_bytes):
        with pytest.raises(DocumentParsingError):
            DOCXParser().parse(b"not a real docx", "broken.docx")

    def test_table_content_is_not_silently_dropped(self, fixture_bytes):
        # Regression guard: the pre-overhaul parser only ever read
        # document.paragraphs, so anything laid out in a Word table
        # (a common way to present Skills) vanished entirely.
        parsed = DOCXParser().parse(fixture_bytes("sample_cv_table.docx"), "sample_cv_table.docx")

        for skill in ("Python", "Django", "PostgreSQL", "Docker", "Kubernetes", "AWS"):
            assert skill in parsed.raw_text

    def test_table_rows_appear_in_true_document_order_relative_to_paragraphs(self, fixture_bytes):
        parsed = DOCXParser().parse(fixture_bytes("sample_cv_table.docx"), "sample_cv_table.docx")
        assert parsed.raw_text.index("Skills") < parsed.raw_text.index("Python")

    def test_word_heading_style_is_captured_as_is_heading_style(self, fixture_bytes):
        parsed = DOCXParser().parse(
            fixture_bytes("sample_cv_heading_styles.docx"), "sample_cv_heading_styles.docx"
        )
        heading_lines = [line for line in parsed.line_records if line.is_heading_style]
        heading_texts = {line.text for line in heading_lines}

        assert "Professional Experience" in heading_texts
        assert "Technical Skills" in heading_texts
        # A normal paragraph must not be misidentified as a heading style.
        assert not any(
            line.is_heading_style for line in parsed.line_records if "Senior Engineer" in line.text
        )

    def test_french_docx_extracts_correctly(self, fixture_bytes):
        parsed = DOCXParser().parse(fixture_bytes("sample_cv_fr.docx"), "sample_cv_fr.docx")
        assert "Camille Dubois" in parsed.raw_text
        assert "EXPERIENCE PROFESSIONNELLE" in parsed.raw_text
