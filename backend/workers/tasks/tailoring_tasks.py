"""Tailoring execution task (Phase 5 sections 35-36). Mirrors
workers/tasks/analysis_tasks.py's shape and retry rationale exactly - a
single task per tailoring run, retried only on genuinely unexpected
failures (a rejected/unsupported claim is a normal, successful
completion outcome for that one change, not an exception - section 36:
"do not retry validation failures indefinitely").

Idempotency: the task always operates on an existing `plan_id` (created
synchronously by the API, in PENDING status) - it never creates a new
TailoringPlan itself, and `RunTailoring`/`DjangoTailoringRepository.
save_result` replaces any prior changes for that plan rather than
appending, so a retry can never produce duplicate tailored CVs.
"""
import logging

from config.container import build_run_tailoring
from workers.celery_app import app

logger = logging.getLogger(__name__)


@app.task(name="workers.tailoring.run_tailoring", bind=True, max_retries=2, default_retry_delay=10)
def run_tailoring(self, plan_id: str) -> None:
    try:
        build_run_tailoring().execute(plan_id)
    except Exception as exc:
        logger.warning("tailoring.retry plan_id=%s attempt=%s", plan_id, self.request.retries)
        raise self.retry(exc=exc) from exc
