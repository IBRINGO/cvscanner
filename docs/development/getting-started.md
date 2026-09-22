# Getting Started (Local Development)

See the root [README.md](../../README.md) for the full setup, environment
variables, and command reference. This file covers day-to-day development
notes that don't belong in the top-level README.

## Recommended workflow

1. `make up` — start Postgres, Redis, backend, worker, and frontend via
   Docker Compose.
2. Backend code changes are picked up automatically (`runserver` with a
   volume mount); Angular changes are picked up by the Angular dev server's
   live reload.
3. Run `make test` before opening a pull request.
4. Run `make lint` to check formatting/static analysis on both projects.

## Running services individually (without Docker)

Useful when iterating quickly on just the backend or just the frontend. See
the "Backend" and "Frontend" sections of the root README for the exact
commands (virtualenv + `manage.py runserver`, or `npm start`).

## Adding a new backend module

1. Decide which layer the code belongs to (`domain`, `application`,
   `infrastructure`, `interfaces`) — see
   [dependency-rule.md](../architecture/dependency-rule.md).
2. If it needs persistence, add/extend a Django app under `apps/` and write
   a migration.
3. Never import Django or a vendor SDK from `domain/`.

## Adding a new frontend feature

1. Create the feature under `frontend/src/app/features/<name>/` with the
   standard `pages/ components/ services/ store/ models/` sub-structure.
2. Register routes in `app.routes.ts` using lazy loading.
3. Reuse `core/http` for all backend calls — never hardcode the API base
   URL in a feature service.
