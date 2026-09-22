import pytest

from domain.documents.exceptions import DocumentParsingError
from infrastructure.document_processing.parsers.plain_text_parser import PlainTextParser


class TestPlainTextParser:
    def test_extracts_raw_text(self, fixture_bytes):
        parsed = PlainTextParser().parse(fixture_bytes("sample_job_offer.txt"), "sample_job_offer.txt")

        assert "Senior Backend Engineer" in parsed.raw_text
        assert parsed.pages == []

    def test_empty_text_raises_parsing_error(self):
        with pytest.raises(DocumentParsingError):
            PlainTextParser().parse(b"   \n  ", "empty.txt")

    def test_non_utf8_bytes_raise_parsing_error(self):
        with pytest.raises(DocumentParsingError):
            PlainTextParser().parse(b"\xff\xfe\x00\x01", "binary.txt")
