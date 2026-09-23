"""Analysis processing task (Phase 4 section 36). Mirrors
workers/tasks/document_tasks.py's shape and retry rationale: a single
task per analysis run, retried only on genuinely transient failures.

Idempotency (section 37): the task always operates on an existing
`analysis_id` (created synchronously by the API, in PENDING status) - it
never creates a new Analysis row itself, so a retried task simply re-runs
the same pipeline against the same row.
`application.matching.run_analysis.RunAnalysis.save_result` replaces any
prior requirement evaluations for that analysis rather than appending,
so a retry can never produce duplicates.
"""
import logging

from config.container import build_run_analysis
from workers.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="workers.analyses.run_analysis", bind=True, max_retries=2, default_retry_delay=10)
def run_analysis(self, analysis_id: str) -> None:
    try:
        build_run_analysis().execute(analysis_id)
    except Exception as exc:
        logger.warning("analysis.retry analysis_id=%s attempt=%s", analysis_id, self.request.retries)
        raise self.retry(exc=exc) from exc
