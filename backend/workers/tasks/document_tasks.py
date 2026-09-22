"""Document processing tasks (section 27 of the Phase 2 brief).

Deliberately just two tasks (one per document type) rather than one task
per pipeline stage (validate/parse/extract/normalize) - the brief
explicitly allows combining steps ("do not create dozens of tiny Celery
tasks without a reason"), and the pipeline stages share one unit of work
that only makes sense to retry together.

Retries: only genuinely transient failures (anything NOT a
DocumentValidationError/DocumentParsingError, which the pipeline already
turns into a FAILED status without raising) reach the `except Exception`
branch and get retried - a corrupted PDF will never succeed on retry, so
it is not retried; a database hiccup might.
"""
import logging

from config.container import build_cv_processing_pipeline, build_job_processing_pipeline
from workers.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="workers.documents.process_cv_document", bind=True, max_retries=2, default_retry_delay=10)
def process_cv_document(self, document_id: str) -> None:
    try:
        build_cv_processing_pipeline().run(document_id)
    except Exception as exc:
        logger.warning("cv.process.retry document_id=%s attempt=%s", document_id, self.request.retries)
        raise self.retry(exc=exc) from exc


@app.task(name="workers.documents.process_job_document", bind=True, max_retries=2, default_retry_delay=10)
def process_job_document(self, document_id: str) -> None:
    try:
        build_job_processing_pipeline().run(document_id)
    except Exception as exc:
        logger.warning("job.process.retry document_id=%s attempt=%s", document_id, self.request.retries)
        raise self.retry(exc=exc) from exc
