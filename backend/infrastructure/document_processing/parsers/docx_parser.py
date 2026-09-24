"""DOCX parsing via python-docx.

DOCX has no reliable notion of "page number" without actually laying out
the document (python-docx does not do pagination) - every ParsedBlock/
LineRecord here has page_number=None rather than a fabricated guess. See
domain/documents/entities.py's ParsedBlock docstring and section 12 of
the Phase 2 brief ("never fabricate provenance").

Empty paragraphs are kept in `raw_text` (not stripped): a blank paragraph
between two CV entries is the same "there was a blank line here" signal
domain/cv/policies.py's block-splitting depends on (see pdf_parser.py's
docstring for the PDF equivalent of this problem). `blocks`, on the other
hand, only includes non-empty paragraphs - an empty ParsedBlock is not a
meaningful unit on its own.

Document-intelligence overhaul additions:

    - Paragraphs and tables are walked in true document order (python-
      docx's own `document.paragraphs`/`document.tables` are two
      *separate* lists that lose their relative position - `_iter_block_items`
      walks the underlying XML body instead, the standard python-docx
      pattern for this). A table's rows are flattened into " | "-joined
      lines rather than silently dropped, which the pre-overhaul parser
      did entirely (it only ever read `document.paragraphs`).
    - A paragraph's Word style name (e.g. "Heading 1") is captured as
      `is_heading_style` - an author-marked heading is a near-certain
      signal domain/cv/policies.py's heading scoring now uses directly,
      instead of DOCX headings having to look heading-shaped as plain
      text the same way a PDF line does.
    - Run-level bold/size are captured too (best-effort - a run inherits
      its style's size when not set explicitly, which python-docx does
      not resolve for us; None simply means "not explicitly set on this
      run", not "not bold/normal size").
"""
import io
from statistics import median

from docx import Document as DocxDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from domain.documents.entities import LineRecord, ParsedBlock, ParsedDocument
from domain.documents.exceptions import DocumentParsingError

_HEADING_STYLE_PREFIXES = ("heading", "title")


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

        all_texts: list[str] = []
        line_records: list[LineRecord] = []
        blocks: list[ParsedBlock] = []
        position = 0

        for item in _iter_block_items(document):
            if isinstance(item, Paragraph):
                text = item.text
                all_texts.append(text)
                font_size, is_bold = _paragraph_font_info(item)
                is_heading_style = _is_heading_style(item.style.name if item.style else None)
                line_records.append(
                    LineRecord(
                        page_number=None,
                        text=text,
                        font_size=font_size,
                        is_bold=is_bold,
                        is_heading_style=is_heading_style,
                    )
                )
                if text.strip():
                    blocks.append(
                        ParsedBlock(
                            text=text,
                            page_number=None,
                            position=position,
                            font_size=font_size,
                            is_bold=is_bold,
                            is_heading_style=is_heading_style,
                        )
                    )
                    position += 1
            else:
                for row_text in _table_row_texts(item):
                    all_texts.append(row_text)
                    line_records.append(LineRecord(page_number=None, text=row_text))
                    blocks.append(ParsedBlock(text=row_text, page_number=None, position=position))
                    position += 1
                # A blank line after the table, same reasoning as an empty
                # paragraph: a visual break the block-splitter should see.
                all_texts.append("")
                line_records.append(LineRecord(page_number=None, text=""))

        raw_text = "\n".join(all_texts)

        if not raw_text.strip():
            raise DocumentParsingError(f"DOCX '{filename}' contains no extractable text.")

        return ParsedDocument(
            raw_text=raw_text,
            pages=[],  # no reliable page boundaries for DOCX
            blocks=blocks,
            line_records=line_records,
            metadata={"parser": "python-docx", "paragraph_count": len(blocks)},
        )


def _iter_block_items(document):
    """Yields the document body's paragraphs and tables in true document
    order. `document.paragraphs`/`document.tables` are separate flat
    lists that lose their relative position to each other - this walks
    the underlying XML body directly instead (the standard python-docx
    recipe for this, since the library doesn't expose it itself).
    """
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def _table_row_texts(table: Table) -> list[str]:
    rows: list[str] = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
        if cells:
            rows.append(" | ".join(cells))
    return rows


def _is_heading_style(style_name: str | None) -> bool:
    if not style_name:
        return False
    return style_name.strip().lower().startswith(_HEADING_STYLE_PREFIXES)


def _paragraph_font_info(paragraph: Paragraph) -> tuple[float | None, bool | None]:
    sizes = [run.font.size.pt for run in paragraph.runs if run.font.size is not None]
    bold_flags = [run.bold for run in paragraph.runs if run.bold is not None]
    font_size = median(sizes) if sizes else None
    is_bold = any(bold_flags) if bold_flags else None
    return font_size, is_bold
