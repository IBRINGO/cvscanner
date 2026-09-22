"""Orchestrates the full job-offer processing pipeline. Mirrors
application/cv/process_pipeline.py - see that module's docstring for the
idempotency and error-handling rationale, which applies identically here.
"""
import logging
import time

from domain.cv.policies import detect_sections
from domain.documents.enums import ProcessingStatus
from domain.documents.exceptions import DocumentParsingError, DocumentValidationError

logger = logging.getLogger(__name__)

EXTRACTION_VERSION = "1.0.0"


class ProcessJobDocumentPipeline:
    def __init__(self, document_repository, parse_document, extract_job_profile) -> None:
        self._repository = document_repository
        self._parse_document = parse_document
        self._extract_job_profile = extract_job_profile

    def run(self, document_id: str) -> None:
        document = self._repository.get(document_id)

        if document.status == ProcessingStatus.PROCESSED:
            logger.info("job.process.skip_already_processed document_id=%s", document_id)
            return

        started_at = time.monotonic()
        try:
            self._repository.update_status(document_id, ProcessingStatus.VALIDATING)
            self._repository.update_status(document_id, ProcessingStatus.PROCESSING)

            parsed = self._parse_document.execute(document_id, document.mime_type, document.original_filename)
            sections = detect_sections(parsed)
            self._repository.save_parsed_result(
                document_id,
                raw_text=parsed.raw_text,
                page_count=parsed.page_count,
                sections=[_section_to_dict(section) for section in sections],
            )

            self._extract_job_profile.execute(document_id, parsed, sections)

            self._repository.update_processing_metadata(document_id, extraction_version=EXTRACTION_VERSION)
            self._repository.update_status(document_id, ProcessingStatus.PROCESSED)
            logger.info(
                "job.process.success document_id=%s duration_s=%.3f",
                document_id,
                time.monotonic() - started_at,
            )
        except (DocumentValidationError, DocumentParsingError) as exc:
            self._repository.mark_failed(document_id, str(exc))
            logger.warning("job.process.failed document_id=%s reason=%s", document_id, exc)
        except Exception:
            self._repository.mark_failed(
                document_id, "An unexpected error occurred while processing this document."
            )
            logger.exception("job.process.unexpected_error document_id=%s", document_id)
            raise


def _section_to_dict(section) -> dict:
    return {
        "type": section.section_type.value,
        "heading": section.heading_text,
        "page_number": section.page_number,
    }
