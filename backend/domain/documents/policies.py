"""Business rules about documents that have nothing to do with Django,
storage, or parsing libraries: what makes an upload valid, and what
status transitions are legal.
"""
from domain.documents.enums import ProcessingStatus
from domain.documents.exceptions import DocumentValidationError

# Phase 2 only claims support for what is actually implemented. Do not add
# a mime type here without a matching parser in
# infrastructure/document_processing/parsers/.
SUPPORTED_MIME_TYPES: dict[str, str] = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_FILE_SIZE_BYTES = 1  # reject genuinely empty uploads


def validate_file(
    *, filename: str, mime_type: str, size_bytes: int
) -> None:
    """Raises DocumentValidationError if the upload does not meet the
    Phase 2 baseline (section 9 of the Phase 2 brief). Never raises for
    reasons the caller can't act on (e.g. it never tries to read file
    content - that's the parser's job, and parser failures map to
    ProcessingStatus.FAILED, not a 4xx rejection at upload time).
    """
    if size_bytes < MIN_FILE_SIZE_BYTES:
        raise DocumentValidationError("The uploaded file is empty.")

    if size_bytes > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise DocumentValidationError(f"The uploaded file exceeds the {max_mb} MB limit.")

    if mime_type not in SUPPORTED_MIME_TYPES:
        raise DocumentValidationError(
            "Unsupported file type. CVScanner currently accepts PDF and DOCX files only."
        )

    expected_extension = SUPPORTED_MIME_TYPES[mime_type]
    if not filename.lower().endswith(expected_extension):
        raise DocumentValidationError(
            f"The file extension does not match its content type "
            f"(expected {expected_extension})."
        )


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------
_ALLOWED_TRANSITIONS: dict[ProcessingStatus, frozenset[ProcessingStatus]] = {
    ProcessingStatus.UPLOADED: frozenset({ProcessingStatus.VALIDATING, ProcessingStatus.FAILED}),
    ProcessingStatus.VALIDATING: frozenset(
        {ProcessingStatus.PROCESSING, ProcessingStatus.FAILED}
    ),
    ProcessingStatus.PROCESSING: frozenset(
        {ProcessingStatus.PROCESSED, ProcessingStatus.FAILED}
    ),
    ProcessingStatus.PROCESSED: frozenset({ProcessingStatus.PROCESSING}),  # reprocessing
    ProcessingStatus.FAILED: frozenset({ProcessingStatus.VALIDATING}),  # retry from the top
}


def can_transition(current: ProcessingStatus, target: ProcessingStatus) -> bool:
    if current == target:
        return True  # idempotent no-op transitions are always allowed
    return target in _ALLOWED_TRANSITIONS.get(current, frozenset())
