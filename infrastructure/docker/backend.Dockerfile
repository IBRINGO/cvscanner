# Development image for the Django backend and the Celery worker (same
# image, different `command:` in docker-compose.yml). Not a production
# image — there is no multi-stage build/gunicorn here yet; see
# config/settings/production.py for what a real deployment would still
# need on top of this (a WSGI server, static file collection, etc.).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install -e ".[dev]"

COPY backend/ .
COPY infrastructure/docker/backend-entrypoint.sh /usr/local/bin/backend-entrypoint.sh
RUN chmod +x /usr/local/bin/backend-entrypoint.sh

ENTRYPOINT ["backend-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
