"""Celery application for CVScanner.

Run a worker locally with:

    celery -A workers.celery_app worker --loglevel=info

(from the `backend/` directory, with the virtualenv activated and
`DJANGO_SETTINGS_MODULE` set — see the root README).
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("cvscanner")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(["workers"])
