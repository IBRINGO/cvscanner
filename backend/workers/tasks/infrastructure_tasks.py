"""Infrastructure smoke-test tasks.

`ping` is NOT part of the future ATS pipeline (see cv_tasks.py,
job_tasks.py, etc. in later phases) — it exists solely to verify that
Django -> Celery -> Redis -> worker actually works end-to-end in this
environment.
"""
from workers.celery_app import app


@app.task(name="workers.infrastructure.ping")
def ping() -> str:
    return "pong"
