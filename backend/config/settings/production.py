"""Production settings.

Everything security-sensitive here is required to come from the
environment — there is no hardcoded fallback for SECRET_KEY, and DEBUG can
never be forced on.
"""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

SECRET_KEY = env("DJANGO_SECRET_KEY")  # no default: fail loudly if missing
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")  # no default: must be explicit

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 30)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

CORS_ALLOW_ALL_ORIGINS = False  # CORS_ALLOWED_ORIGINS from base.py must be set explicitly
