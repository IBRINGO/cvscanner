# workers/

Celery application and asynchronous task definitions.

- `celery_app.py` — the Celery app, configured from Django settings
  (`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`, both derived from
  `REDIS_URL`).
- `tasks/infrastructure_tasks.py` — a single `ping` task used only to prove
  the Django → Celery → Redis → worker path works locally. It is
  explicitly **not** part of the future ATS pipeline.
- `tasks/{cv,job,embedding,analysis,recommendation,tailoring}_tasks.py` —
  reserved for Phase 2+ (CV/job parsing, embeddings, analysis,
  recommendations, tailoring). Not implemented yet.
- `workflows/{cv,job,analysis}_pipeline.py` — reserved for Phase 2+
  multi-step orchestration (e.g. parse → normalize → embed). Not
  implemented yet.

## Running a worker locally

```bash
cd backend
celery -A workers.celery_app worker --loglevel=info
```

## Verifying the ping task

```bash
python manage.py shell -c "from workers.tasks.infrastructure_tasks import ping; print(ping.delay().get(timeout=5))"
```
