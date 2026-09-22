# CVScanner

CVScanner is an intelligent ATS (Applicant Tracking System) analysis
platform. A user uploads a CV and a job offer; the platform parses both,
extracts structured information, matches the candidate against the job's
requirements, produces an explainable score, and recommends improvements
(including, eventually, a tailored CV with claims validated against
evidence).

**This repository is at Phase 1: Project Foundations.** The ATS
Intelligence Engine itself (parsing, matching, scoring, recommendations,
tailoring) is not implemented yet — see [Roadmap](#roadmap) and
[Known limitations](#known-limitations).

## Architecture

```text
┌─────────────┐        HTTP/JSON        ┌──────────────────┐
│   Angular    │ ───────────────────────▶│  Django + DRF     │
│  (frontend)  │◀─────────────────────── │  (backend API)    │
└─────────────┘                          └─────────┬────────┘
                                                    │
                                    ┌───────────────┼────────────────┐
                                    ▼               ▼                ▼
                              ┌───────────┐   ┌───────────┐   ┌────────────┐
                              │ PostgreSQL │   │   Redis   │   │   Celery   │
                              └───────────┘   └───────────┘   └────────────┘
```

The backend is a **modular monolith**: one deployable Django project,
internally organized into `domain/` → `application/` → `interfaces/`
layers with `infrastructure/` implementing abstractions the other layers
depend on. See [docs/architecture/overview.md](docs/architecture/overview.md),
[docs/architecture/dependency-rule.md](docs/architecture/dependency-rule.md),
and [docs/adr/0001-modular-monolith-and-monorepo.md](docs/adr/0001-modular-monolith-and-monorepo.md)
for the full reasoning.

## Repository structure

```text
cvscanner/
├── frontend/         Angular app (feature-based architecture)
├── backend/          Django + DRF API, Celery workers, domain/application/infrastructure
├── docs/             Architecture docs, ADRs, API docs, dev notes
├── infrastructure/   Dockerfiles and local-environment scripts
├── docker-compose.yml       Base service definitions
├── docker-compose.dev.yml   Local dev overrides (bind mounts, DEBUG)
├── Makefile          Local development commands
└── .env.example      Environment variable reference
```

## Requirements

| Tool           | Version used in this repo | Notes                                   |
|----------------|---------------------------|------------------------------------------|
| Node.js        | 20.16.0                   | Angular CLI 19 requires `^20.11.1`        |
| npm            | 10.9.2                    |                                            |
| Python         | 3.12.5                    |                                            |
| Docker         | 28.0.1                    | with Docker Compose v2.33+                |
| Git            | 2.45.2                    |                                            |

Angular 19 (not 20) was chosen because Angular CLI 20 requires Node
`^20.19.0`, which is newer than the Node 20.16.0 available in this
environment — see [ADR 0001](docs/adr/0001-modular-monolith-and-monorepo.md).
Django 5.2 (the current LTS release) was chosen over the newer, non-LTS
6.1 line for stability.

## Local setup

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

   Adjust `POSTGRES_PASSWORD` and `DJANGO_SECRET_KEY` at minimum. Never
   commit `.env`.

2. Start everything with Docker Compose (recommended):

   ```bash
   make up
   # equivalent to:
   # docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
   ```

   This starts `postgres`, `redis`, `backend` (:8000), `worker` (Celery),
   and `frontend` (:4200). The backend entrypoint runs migrations
   automatically before starting.

3. Open the frontend at http://localhost:4200 — the dashboard page calls
   `GET http://localhost:8000/api/v1/health/` and shows whether the
   backend is reachable.

### Running services individually (without Docker)

Useful for fast iteration on just one side. Backend and worker need a
Postgres/Redis reachable at `localhost` — either run `docker compose up
postgres redis` first, or point `backend/.env` (see
`backend/.env.example`) at your own instances.

```bash
# Backend
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"
python manage.py migrate
python manage.py runserver 0.0.0.0:8000

# Frontend (separate terminal)
cd frontend
npm install
npm start

# Celery worker (separate terminal, same venv as backend)
cd backend && source .venv/Scripts/activate
celery -A workers.celery_app worker --loglevel=info
```

Or via the Makefile: `make backend`, `make frontend`, `make worker`,
`make migrate`.

## Environment variables

See [.env.example](.env.example) for the full list (Postgres, Redis,
Django, CORS, and the frontend's `API_BASE_URL`). Variables for future
phases (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `S3_*`) are documented there
but unused in Phase 1.

## Running tests

```bash
make test            # both projects
make test-backend    # pytest, SQLite in-memory — no services required
make test-frontend   # Karma/Jasmine, headless Chrome required
```

## Linting / type-checking

```bash
make lint             # both projects
make lint-backend     # ruff + black --check
make lint-frontend    # tsc --noEmit (no ESLint config yet, see Known limitations)
```

## Docker

```bash
make up      # build + start everything
make down    # stop everything
make build   # rebuild images without starting
make logs    # follow logs from every service
```

`docker-compose.yml` defines the five services (`postgres`, `redis`,
`backend`, `worker`, `frontend`) without source bind-mounts, so it stays
reusable as a base for a future staging/production compose file.
`docker-compose.dev.yml` adds the bind-mounts and `DJANGO_DEBUG=true`
needed for local live-reload — the Makefile always merges both files.

## Backend

Django + Django REST Framework, organized as a modular monolith:

- `config/` — settings (`base` / `development` / `testing` / `production`), root URLs, WSGI/ASGI.
- `apps/` — Django app configs + persistence models (`users`, `documents`, `candidates`, `jobs`, `skills`, `analyses`, `recommendations`, `tailoring`, `audit`). No models are defined yet.
- `domain/`, `application/`, `infrastructure/`, `interfaces/` — the Clean Architecture layers; see the dependency-rule doc linked above. Only `interfaces/api/v1/health/` has real logic in Phase 1.
- `workers/` — Celery app + a single infrastructure smoke-test task (`ping`).
- `tests/` — pytest suite (`api/`, `unit/`, `integration/`), mirroring the structure the ATS Intelligence Engine will use in later phases.

API versioning starts at `/api/v1/`. The only endpoint today is
`GET /api/v1/health/`.

## Frontend

Angular 19, standalone components, feature-based architecture:

- `core/` — app-wide infrastructure: `config` (typed `APP_CONFIG`, backed by `src/environments/`), `http` (`ApiClientService` + auth/error/loading interceptors), `auth` (models/store/service/guard — **not implemented**, see Known limitations), `services` (notification, file-upload, download).
- `shared/` — reusable, feature-agnostic UI (`components/ui/placeholder-page` today) and utilities.
- `layout/` — `MainLayoutComponent` (header + sidebar + router-outlet + footer) used by every route; `AuthLayoutComponent` reserved for future login/signup pages.
- `features/` — one folder per product capability (`dashboard`, `cvs`, `jobs`, `analysis`, `recommendations`, `tailoring`, `applications`, `settings`), each lazy-loaded from `app.routes.ts`. Only `dashboard` has real logic (the health-check widget); the rest render a shared placeholder page.

## Celery

`workers/celery_app.py` configures Celery from Django settings
(`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`, both derived from
`REDIS_URL`). `workers/tasks/infrastructure_tasks.py` defines `ping`, used
only to prove the Django → Celery → Redis → worker path works — it is not
part of the future ATS pipeline. See [backend/workers/README.md](backend/workers/README.md).

## Development guidelines

- Follow the dependency rule: `interfaces → application → domain`, with
  `infrastructure` implementing abstractions those layers define. `domain/`
  must never import Django, DRF, Celery, or a vendor SDK.
- Feature code (frontend or backend) must go through `core/`
  (`ApiClientService`, `APP_CONFIG`) rather than hardcoding URLs.
- New Django apps/domain modules should follow the existing folder
  conventions — see [docs/development/getting-started.md](docs/development/getting-started.md).
- No fake functionality: unimplemented features are represented honestly
  (a placeholder page, a "not implemented" error) rather than mocked data.

## Known limitations

- **Authentication is not implemented.** `core/auth/` exists as a
  structural placeholder (`AuthService.login()` always throws,
  `authGuard` always allows navigation) so later phases can wire in real
  auth without moving files.
- **No ESLint configuration for the frontend** — Angular 19's `ng new` no
  longer scaffolds one by default. `make lint-frontend` runs TypeScript's
  type-checker instead; adding ESLint is left for when the team defines a
  house style, rather than adopting Angular CLI's defaults speculatively.
- **`black --check` fails in this environment** on Python 3.12.5 due to a
  [known CPython AST safety issue](https://github.com/psf/black) that
  Black refuses to run under; it works on 3.12.6+ or 3.12.4-. `ruff check`
  (the more substantial static-analysis pass) is unaffected and passes.
- **No ATS Intelligence Engine yet** — no CV/job parsing, matching,
  scoring, recommendations, or tailoring. `domain/`, `application/`, and
  `infrastructure/` only contain the package boundaries (see their
  respective `README.md`) for Phases 2–5 to fill in.
- **No production Dockerfile/compose** — `infrastructure/docker/*.Dockerfile`
  and `docker-compose*.yml` are development-only (dev servers, bind
  mounts). `config/settings/production.py` exists for a future deployment
  but isn't exercised by anything in this repository yet.

## Roadmap

- **Phase 2** — PDF/DOCX parsing, structured `CandidateProfile`/`JobProfile`, skill normalization.
- **Phase 3** — embeddings, `pgvector`, hybrid (lexical + semantic) search, evidence retrieval.
- **Phase 4** — deterministic, explainable scoring engine, gap analysis, recommendations.
- **Phase 5** — LLM-assisted explanations, CV tailoring, and claim validation ("truth layer").
