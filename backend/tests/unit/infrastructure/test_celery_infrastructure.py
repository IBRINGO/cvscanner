"""Verifies the Celery/Redis wiring, not any ATS behaviour.

`CELERY_TASK_ALWAYS_EAGER` (set in config/settings/testing.py) runs the
task synchronously in-process, so this test does not require a running
Redis broker or worker — it only proves the task is registered and
executable through the Celery app.
"""
from workers.tasks.infrastructure_tasks import ping


def test_ping_task_executes_and_returns_pong():
    result = ping.delay()

    assert result.get(timeout=5) == "pong"
