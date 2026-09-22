# infrastructure/

Docker build assets and local-environment scripts referenced by the
root `docker-compose.yml` / `docker-compose.dev.yml`.

- `docker/backend.Dockerfile` — shared image for the `backend` (Django/DRF)
  and `worker` (Celery) services.
- `docker/backend-entrypoint.sh` — runs migrations before starting either
  the API server or the worker.
- `docker/frontend.Dockerfile` — Angular dev-server image.
- `scripts/` — reserved for one-off local setup scripts as they become
  necessary (e.g. seeding reference data). Empty in Phase 1.
