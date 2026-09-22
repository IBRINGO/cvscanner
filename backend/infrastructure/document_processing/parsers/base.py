"""Parser abstraction (section 10 of the Phase 2 brief).

The domain and application layers never know whether a document was read
with pdfplumber, python-docx, or anything else - they only see the
ParsedDocument this Protocol promises to return.
"""
from typing import Protocol

from domain.documents.entities import ParsedDocument


class DocumentParser(Protocol):
    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        """Raises domain.documents.exceptions.DocumentParsingError if
        `content` cannot be read as this parser's format.
        """
        ...
