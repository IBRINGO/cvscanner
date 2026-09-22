class DocumentValidationError(Exception):
    """Raised when an upload fails the Phase 2 validation baseline
    (extension/mime/size). Maps to a 4xx API response - never a 500.
    """


class DocumentParsingError(Exception):
    """Raised by a parser when it cannot extract text from a file it
    otherwise claims to support (corrupted PDF, malformed DOCX, ...).
    The pipeline that catches this marks the document FAILED; it must
    never crash the Celery worker process.
    """


class UnsupportedDocumentFormatError(Exception):
    """Raised when no parser is registered for a document's mime type."""
