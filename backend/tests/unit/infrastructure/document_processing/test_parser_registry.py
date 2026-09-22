import pytest

from domain.documents.exceptions import UnsupportedDocumentFormatError
from infrastructure.document_processing.parsers.docx_parser import DOCXParser
from infrastructure.document_processing.parsers.pdf_parser import PDFParser
from infrastructure.document_processing.parsers.registry import DocumentParserRegistry


class TestDocumentParserRegistry:
    def test_resolves_pdf(self):
        assert isinstance(DocumentParserRegistry().get_parser("application/pdf"), PDFParser)

    def test_resolves_docx(self):
        registry = DocumentParserRegistry()
        parser = registry.get_parser(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert isinstance(parser, DOCXParser)

    def test_unsupported_mime_type_raises(self):
        with pytest.raises(UnsupportedDocumentFormatError):
            DocumentParserRegistry().get_parser("image/png")
