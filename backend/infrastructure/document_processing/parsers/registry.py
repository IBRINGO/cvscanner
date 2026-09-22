"""Maps a mime type to a concrete DocumentParser (section 10).

Application use cases depend on an object with a `get_parser(mime_type)`
method (duck-typed - see application/documents/parse_document.py's
docstring) so they never import PDFParser/DOCXParser directly.
"""
from domain.documents.exceptions import UnsupportedDocumentFormatError
from infrastructure.document_processing.parsers.docx_parser import DOCXParser
from infrastructure.document_processing.parsers.pdf_parser import PDFParser
from infrastructure.document_processing.parsers.plain_text_parser import PlainTextParser


class DocumentParserRegistry:
    def __init__(self) -> None:
        self._parsers = {
            "application/pdf": PDFParser(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXParser(),
            "text/plain": PlainTextParser(),
        }

    def get_parser(self, mime_type: str):
        try:
            return self._parsers[mime_type]
        except KeyError as exc:
            raise UnsupportedDocumentFormatError(
                f"No parser registered for mime type: {mime_type}"
            ) from exc
