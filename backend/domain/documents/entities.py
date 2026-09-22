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

from domain.documents.enums import DocumentType, ProcessingStatus, SectionType


@dataclass(frozen=True)
class ParsedPage:
    """One page of extracted text. `page_number` is 1-indexed."""

    page_number: int
    text: str


@dataclass(frozen=True)
class ParsedBlock:
    """A structural chunk of text (a paragraph, a table cell run, ...).

    `page_number` is None when the source format doesn't have a reliable
    notion of pages (DOCX) - see docs/architecture/phase-2-pipeline.md,
    "never fabricate provenance". `position` is the block's 0-indexed
    sequential order within the document, not a pixel/coordinate position.
    """

    text: str
    page_number: int | None
    position: int


@dataclass(frozen=True)
class ParsedDocument:
    """What every concrete parser (PDFParser, DOCXParser, ...) must produce."""

    raw_text: str
    pages: list[ParsedPage] = field(default_factory=list)
    blocks: list[ParsedBlock] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def page_count(self) -> int | None:
        return len(self.pages) if self.pages else None


@dataclass(frozen=True)
class DetectedSection:
    """One heading-delimited region of a parsed document.

    Produced by domain/cv/policies.py::detect_sections. `heading_text` is
    kept verbatim (e.g. "Professional Experience") alongside the
    normalized `section_type` (EXPERIENCE) so evidence can cite exactly
    what the document said.
    """

    section_type: SectionType
    heading_text: str
    body_text: str
    page_number: int | None


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
