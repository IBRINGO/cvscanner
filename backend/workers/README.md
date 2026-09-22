# workers/

Celery application and asynchronous task definitions.

- `celery_app.py` - the Celery app, configured from Django settings
  (`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`, both derived from
  `REDIS_URL`).
- `tasks/infrastructure_tasks.py` - a single `ping` task used only to prove
  the Django -> Celery -> Redis -> worker path works locally. It is
  explicitly **not** part of the ATS pipeline.
- `tasks/document_tasks.py` - `process_cv_document` and
  `process_job_document`: each runs the full validate/parse/detect
  sections/extract/normalize/persist pipeline for one document, then
  the Phase 3 semantic enrichment/embedding step (see
  [docs/architecture/phase-2-pipeline.md](../../docs/architecture/phase-2-pipeline.md)
  and
  [docs/architecture/phase-3-semantics.md](../../docs/architecture/phase-3-semantics.md)).
  A failure in the Phase 3 step is caught inside the pipeline and never
  fails the task - the document still ends up `PROCESSED`.
  One task per document type rather than one task per pipeline stage -
  the stages only make sense to retry together. Both tasks are thin: the
  actual orchestration lives in `application/cv/process_pipeline.py` and
  `application/jobs/process_pipeline.py` so it can be unit-tested without
  Celery.
- `workflows/` - reserved for Phase 3+ multi-step orchestration that
  spans multiple documents (e.g. a matching run over a CV and a job
  offer together). Not implemented yet; Phase 2's pipeline is
  single-document and lives in `application/*/process_pipeline.py`
  instead of here.

## Running a worker locally

```bash
cd backend
celery -A workers.celery_app worker --loglevel=info
```

On Windows, Celery's default process pool does not work reliably; use
the solo pool for local development:

```bash
celery -A workers.celery_app worker --loglevel=info --pool=solo
```

## Verifying the ping task

```bash
python manage.py shell -c "from workers.tasks.infrastructure_tasks import ping; print(ping.delay().get(timeout=5))"
```

## Verifying document processing

Requires Redis running and a worker started (see above):

```bash
python manage.py shell -c "
from domain.documents.enums import DocumentType
from config.container import build_upload_document
content = open('tests/fixtures/sample_cv.pdf', 'rb').read()
result = build_upload_document().execute(document_type=DocumentType.CV, content=content, original_filename='sample_cv.pdf', mime_type='application/pdf')
print(result.document.id, result.needs_processing)
"
```

Then enqueue processing via `workers.tasks.document_tasks.process_cv_document.delay(<id>)`,
or simply upload through `POST /api/v1/cvs/`, which enqueues it
automatically.
