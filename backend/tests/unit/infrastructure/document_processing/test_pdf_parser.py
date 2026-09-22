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
