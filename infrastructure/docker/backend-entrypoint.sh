#!/bin/sh
set -e

# Applies to both the `backend` and `worker` services (they share this
# image). Migrations only need to run once, but running them again is a
# no-op, so it's simplest to always run them before either the API server
# or the Celery worker starts.
python manage.py migrate --noinput

exec "$@"
