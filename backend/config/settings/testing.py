"""Settings used by the automated test suite (pytest-django / CI).

Uses an in-memory SQLite database so tests don't require a running
PostgreSQL instance, and runs Celery tasks eagerly (synchronously) so
worker infrastructure doesn't need to be up for tests either.
"""
from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "test-secret-key-not-for-production"
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
