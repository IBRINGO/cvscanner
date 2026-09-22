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
