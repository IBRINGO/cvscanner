"""Intermediate representation produced by a parser, before any structured
profile exists.

Pipeline this module supports (see docs/architecture/phase-2-pipeline.md):

    RAW DOCUMENT (bytes)
          v
    ParsedDocument (this module)   <- infrastructure/document_processing/parsers/
          v
    list[DetectedSection] (this module)   <- domain/cv/policies.py
          v
    CandidateProfile / JobProfile   <- domain/cv, domain/job

These are plain dataclasses. Nothing here reads a file, calls a database,
or knows which parsing library produced it.
"""
from dataclasses import dataclass, field
from datetime import datetime

from domain.documents.enums import DocumentLanguage, DocumentType, ProcessingStatus, SectionType
from domain.documents.language import DetectedLanguage


@dataclass(frozen=True)
class ParsedPage:
    """One page of extracted text. `page_number` is 1-indexed."""

    page_number: int
    text: str


@dataclass(frozen=True)
class BoundingBox:
    """A block's position on a page, in PDF points (top-left origin,
    matching pdfplumber's coordinate system). Never fabricated for
    formats without real layout coordinates (DOCX) - see ParsedBlock.bbox.
    """

    x0: float
    x1: float
    top: float
    bottom: float


@dataclass(frozen=True)
class ParsedBlock:
    """A structural chunk of text (a paragraph, a table cell run, ...).

    `page_number` is None when the source format doesn't have a reliable
    notion of pages (DOCX) - see docs/architecture/phase-2-pipeline.md,
    "never fabricate provenance". `position` is the block's 0-indexed
    sequential order within the document, not a pixel/coordinate position
    - `bbox`/`column_index` (added for the document-intelligence overhaul,
    all optional/default-None so existing construction sites keep
    working unchanged) carry the *actual* spatial position when the
    parser has one (PDF); DOCX has no coordinates so leaves them None but
    can still populate `font_size`/`is_bold`/`is_heading_style` from the
    run/paragraph's own formatting.

    `column_index` is 0-based, left-to-right, only set by parsers that
    performed layout/column analysis (see infrastructure/document_processing/
    parsers/pdf_parser.py); None means "not analyzed" (DOCX, or a PDF
    page confidently detected as single-column), not "column 0" -
    downstream code must not conflate the two.
    """

    text: str
    page_number: int | None
    position: int
    bbox: BoundingBox | None = None
    column_index: int | None = None
    font_size: float | None = None
    is_bold: bool | None = None
    is_heading_style: bool = False


@dataclass(frozen=True)
class LineRecord:
    """One visual line of text plus whatever formatting signal the parser
    could observe for it - the unit domain/cv/policies.py's heading
    detection actually scores (a `ParsedBlock` is a whole paragraph/entry,
    too coarse-grained for per-line heading scoring).

    `column_index` is what makes two-column reading order correct: a
    layout-aware PDF parser emits LineRecords already in the right
    reading order (left column top-to-bottom, then right column
    top-to-bottom - see pdf_parser.py), so detect_sections never needs to
    re-sort anything itself, just walk the list in order. Optional and
    additive: `ParsedDocument.line_records` defaults to `[]`, and
    detect_sections falls back to its pre-overhaul line-splitting of
    `raw_text`/`pages` when empty - every hand-built ParsedDocument in
    existing tests keeps behaving exactly as before.
    """

    page_number: int | None
    text: str
    font_size: float | None = None
    is_bold: bool | None = None
    is_heading_style: bool = False
    column_index: int | None = None


@dataclass(frozen=True)
class ParsedDocument:
    """What every concrete parser (PDFParser, DOCXParser, ...) must produce."""

    raw_text: str
    pages: list[ParsedPage] = field(default_factory=list)
    blocks: list[ParsedBlock] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    language: DetectedLanguage | None = None
    line_records: list[LineRecord] = field(default_factory=list)

    @property
    def page_count(self) -> int | None:
        return len(self.pages) if self.pages else None


@dataclass(frozen=True)
class DetectedSection:
    """One heading-delimited region of a parsed document.

    Produced by domain/cv/policies.py::detect_sections. `heading_text` is
    kept verbatim (e.g. "Professional Experience") alongside the
    normalized `section_type` (EXPERIENCE) so evidence can cite exactly
    what the document said. `confidence` (heading-detection confidence,
    added for the overhaul - see domain/cv/policies.py's heading scoring)
    defaults to 1.0 so every pre-overhaul construction site keeps
    working unchanged.
    """

    section_type: SectionType
    heading_text: str
    body_text: str
    page_number: int | None
    language: DocumentLanguage | None = None
    confidence: float = 1.0
    column_index: int | None = None


@dataclass(frozen=True)
class DocumentRecord:
    """Read-model for a Document (section 7). Repositories return this,
    never a Django model instance, so application code stays framework
    free. `owner_id` is a string (not a User object) since only identity,
    never auth behaviour, is relevant this far from interfaces/.
    """

    id: str
    owner_id: str | None
    document_type: DocumentType
    original_filename: str
    mime_type: str
    file_size: int
    file_hash: str
    status: ProcessingStatus
    page_count: int | None
    processing_metadata: dict
    created_at: datetime
    updated_at: datetime
