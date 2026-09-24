import pytest

from domain.documents.exceptions import DocumentParsingError
from infrastructure.document_processing.parsers.pdf_parser import PDFParser


class TestPDFParser:
    def test_extracts_text_and_pages(self, fixture_bytes):
        parsed = PDFParser().parse(fixture_bytes("sample_cv.pdf"), "sample_cv.pdf")

        assert "Jordan Rivera" in parsed.raw_text
        assert len(parsed.pages) == 1
        assert parsed.page_count == 1

    def test_preserves_blank_line_gap_between_entries(self, fixture_bytes):
        parsed = PDFParser().parse(fixture_bytes("sample_cv.pdf"), "sample_cv.pdf")

        experience_section = parsed.raw_text.split("EXPERIENCE", 1)[1]
        assert "\n\n" in experience_section.split("EDUCATION")[0]

    def test_corrupted_pdf_raises_parsing_error(self, fixture_bytes):
        with pytest.raises(DocumentParsingError):
            PDFParser().parse(fixture_bytes("corrupted.pdf"), "corrupted.pdf")

    def test_empty_pdf_raises_parsing_error(self, fixture_bytes):
        with pytest.raises(DocumentParsingError):
            PDFParser().parse(fixture_bytes("empty.pdf"), "empty.pdf")

    def test_single_column_cv_never_gets_a_column_index(self, fixture_bytes):
        # Regression guard: a normal single-column CV must never be
        # misdetected as two-column - see pdf_parser.py's
        # _detect_column_boundary docstring for the conservative gates
        # that exist specifically to prevent this.
        parsed = PDFParser().parse(fixture_bytes("sample_cv.pdf"), "sample_cv.pdf")

        assert parsed.line_records
        assert all(line.column_index is None for line in parsed.line_records)

    def test_two_column_cv_is_read_left_column_entirely_before_right_column(self, fixture_bytes):
        parsed = PDFParser().parse(
            fixture_bytes("sample_cv_two_column_en.pdf"), "sample_cv_two_column_en.pdf"
        )

        columns = [line.column_index for line in parsed.line_records if line.text.strip()]
        # Once a right-column (1) line appears, no left-column (0) line
        # may appear after it - the whole left column comes first.
        seen_right = False
        for column in columns:
            if column == 1:
                seen_right = True
            elif column == 0 and seen_right:
                pytest.fail(f"a column-0 line appeared after a column-1 line: {columns}")
        assert 0 in columns and 1 in columns

        # And the raw text itself must not interleave the two columns:
        # "SKILLS" and its contents come fully before "EXPERIENCE".
        assert parsed.raw_text.index("SKILLS") < parsed.raw_text.index("EXPERIENCE")
        assert parsed.raw_text.index("Kubernetes") < parsed.raw_text.index("Senior Platform Engineer")

    def test_two_column_french_cv_is_also_read_column_by_column(self, fixture_bytes):
        parsed = PDFParser().parse(
            fixture_bytes("sample_cv_two_column_fr.pdf"), "sample_cv_two_column_fr.pdf"
        )
        assert parsed.raw_text.index("COMPETENCES") < parsed.raw_text.index("EXPERIENCE PROFESSIONNELLE")

    def test_multipage_cv_produces_multiple_pages(self, fixture_bytes):
        parsed = PDFParser().parse(fixture_bytes("sample_cv_multipage.pdf"), "sample_cv_multipage.pdf")
        assert parsed.page_count is not None
        assert parsed.page_count > 1

    def test_captures_font_size_and_boldness_for_lines(self, fixture_bytes):
        parsed = PDFParser().parse(
            fixture_bytes("sample_cv_varied_fonts.pdf"), "sample_cv_varied_fonts.pdf"
        )
        heading_line = next(line for line in parsed.line_records if line.text == "Experience")
        body_line = next(line for line in parsed.line_records if "Lead Engineer" in line.text)

        assert heading_line.font_size is not None
        assert body_line.font_size is not None
        assert heading_line.font_size > body_line.font_size
        assert heading_line.is_bold is True
        assert body_line.is_bold is False
