"""DOCX parsing via python-docx.

DOCX has no reliable notion of "page number" without actually laying out
the document (python-docx does not do pagination) - every ParsedBlock/
ParsedPage here has page_number=None rather than a fabricated guess. See
domain/documents/entities.py's ParsedBlock docstring and section 12 of
the Phase 2 brief ("never fabricate provenance").

Empty paragraphs are kept in `raw_text` (not stripped): a blank paragraph
between two CV entries is the same "there was a blank line here" signal
domain/cv/policies.py's block-splitting depends on (see
pdf_parser.py's docstring for the PDF equivalent of this problem).
`blocks`, on the other hand, only includes non-empty paragraphs - an
empty ParsedBlock is not a meaningful unit on its own.
"""
import io

from docx import Document as DocxDocument
from docx.opc.exceptions import PackageNotFoundError

from domain.documents.entities import ParsedBlock, ParsedDocument
from domain.documents.exceptions import DocumentParsingError


class DOCXParser:
    """Implements infrastructure.document_processing.parsers.base.DocumentParser."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            document = DocxDocument(io.BytesIO(content))
        except PackageNotFoundError as exc:
            raise DocumentParsingError(
                f"Could not parse DOCX '{filename}': not a valid Word document."
            ) from exc
        except Exception as exc:
            raise DocumentParsingError(
                f"Could not parse DOCX '{filename}': {exc.__class__.__name__}."
            ) from exc

        all_paragraphs = [p.text for p in document.paragraphs]
        raw_text = "\n".join(all_paragraphs)

        non_empty = [text for text in all_paragraphs if text.strip()]
        blocks = [
            ParsedBlock(text=text, page_number=None, position=index)
            for index, text in enumerate(non_empty)
        ]

        if not raw_text.strip():
            raise DocumentParsingError(f"DOCX '{filename}' contains no extractable text.")

        return ParsedDocument(
            raw_text=raw_text,
            pages=[],  # no reliable page boundaries for DOCX
            blocks=blocks,
            metadata={"parser": "python-docx", "paragraph_count": len(non_empty)},
        )
