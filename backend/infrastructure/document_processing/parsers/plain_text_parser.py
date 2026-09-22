"""Plain-text parsing (section 23 of the Phase 2 brief: "at minimum,
accept plain text, PDF, and DOCX if the implementation naturally
supports all three"). Job offers are very often pasted as raw text, and
supporting that needs no third-party library - so it is supported for
both CVs and job offers, not just job offers.
"""
from domain.documents.entities import ParsedBlock, ParsedDocument
from domain.documents.exceptions import DocumentParsingError


class PlainTextParser:
    """Implements infrastructure.document_processing.parsers.base.DocumentParser."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DocumentParsingError(f"'{filename}' is not valid UTF-8 text.") from exc

        if not raw_text.strip():
            raise DocumentParsingError(f"'{filename}' contains no text.")

        paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
        blocks = [
            ParsedBlock(text=paragraph, page_number=None, position=index)
            for index, paragraph in enumerate(paragraphs)
        ]

        return ParsedDocument(
            raw_text=raw_text,
            pages=[],
            blocks=blocks,
            metadata={"parser": "plain_text"},
        )
