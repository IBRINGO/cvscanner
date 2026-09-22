"""PDF parsing via pdfplumber.

pdfplumber is built on pdfminer.six (permissive license, pure Python plus
a pypdfium2 wheel for rendering) - no AGPL/vendor lock-in concern, and no
system-level dependency to install. Chosen specifically because it keeps
reliable page boundaries, which is required for page-aware evidence
(section 12 of the Phase 2 brief).

`extract_text()` alone joins every line with a single "\\n" regardless of
how much vertical whitespace separated them on the page - a blank line
between two CV entries (e.g. two Experience blocks) is visually obvious
but textually invisible. `_reconstruct_text_with_gaps` restores it by
comparing each line's vertical gap to the page's typical single-line
gap: a gap of roughly 2x or more means "there was a blank line here",
which is what domain/cv/policies.py's block-splitting (`\\n\\n`) depends
on to separate multiple entries within one section.
"""
import io
from statistics import median

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException

from domain.documents.entities import ParsedBlock, ParsedDocument, ParsedPage
from domain.documents.exceptions import DocumentParsingError

_GAP_MULTIPLIER_FOR_BLANK_LINE = 1.6


class PDFParser:
    """Implements infrastructure.document_processing.parsers.base.DocumentParser."""

    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages: list[ParsedPage] = []
                blocks: list[ParsedBlock] = []
                position = 0

                for index, page in enumerate(pdf.pages, start=1):
                    text = _reconstruct_text_with_gaps(page)
                    pages.append(ParsedPage(page_number=index, text=text))

                    for paragraph in _split_into_blocks(text):
                        blocks.append(
                            ParsedBlock(text=paragraph, page_number=index, position=position)
                        )
                        position += 1

                raw_text = "\n".join(page.text for page in pages)
        except PdfminerException as exc:
            raise DocumentParsingError(
                f"Could not parse PDF '{filename}': corrupted or unreadable content."
            ) from exc
        except Exception as exc:  # pdfplumber/pypdfium2 raise various backend-specific errors
            raise DocumentParsingError(
                f"Could not parse PDF '{filename}': {exc.__class__.__name__}."
            ) from exc

        if not raw_text.strip():
            raise DocumentParsingError(
                f"PDF '{filename}' contains no extractable text "
                "(it may be a scanned image - OCR is not implemented in Phase 2)."
            )

        return ParsedDocument(
            raw_text=raw_text,
            pages=pages,
            blocks=blocks,
            metadata={"parser": "pdfplumber", "page_count": len(pages)},
        )


def _reconstruct_text_with_gaps(page) -> str:
    lines = page.extract_text_lines()
    if not lines:
        return page.extract_text() or ""

    # zip(lines, lines[1:]) intentionally pairs consecutive lines of
    # differing-by-one-element sequences (the classic "sliding pairs"
    # idiom) - strict=False documents that the length mismatch is by
    # design, not an oversight.
    gaps = [
        round(b["top"] - a["top"], 1) for a, b in zip(lines, lines[1:], strict=False) if b["top"] > a["top"]
    ]
    typical_gap = median(gaps) if gaps else 0

    reconstructed: list[str] = [lines[0]["text"]]
    for previous, current in zip(lines, lines[1:], strict=False):
        gap = current["top"] - previous["top"]
        if typical_gap and gap > typical_gap * _GAP_MULTIPLIER_FOR_BLANK_LINE:
            reconstructed.append("")
        reconstructed.append(current["text"])

    return "\n".join(reconstructed)


def _split_into_blocks(text: str) -> list[str]:
    return [block.strip() for block in text.split("\n\n") if block.strip()]
