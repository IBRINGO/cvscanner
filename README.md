# CVScanner

CVScanner is an intelligent ATS (Applicant Tracking System) analysis
platform. A user uploads a CV and a job offer; the platform parses both,
extracts structured information, matches the candidate against the job's
requirements, produces an explainable score, and recommends improvements
(including, eventually, a tailored CV with claims validated against
evidence).

**This repository is at Phase 3: Semantic Intelligence and Knowledge
Enrichment.** CVs and job offers can be uploaded, parsed, and structured
into evidence-backed profiles with normalized skills (Phase 2), which
Phase 3 further enriches: skill relationships and ecosystems, seniority/
education/language normalization, technology mentions scanned from
prose, structured experience requirements, and an optional embedding
foundation. Candidate-job matching, scoring, recommendations, and CV
tailoring are not implemented yet - see [Roadmap](#roadmap) and
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
environment - see [ADR 0001](docs/adr/0001-modular-monolith-and-monorepo.md).
Django 5.2 (the current LTS release) was chosen over the newer, non-LTS
6.1 line for stability. Phase 2 adds `pdfplumber` (PDF text extraction)
and `python-docx` (DOCX text extraction) - see
[docs/architecture/phase-2-pipeline.md](docs/architecture/phase-2-pipeline.md).

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

3. Open the frontend at http://localhost:4200 - the dashboard page calls
   `GET http://localhost:8000/api/v1/health/` and shows whether the
   backend is reachable. From there, **CVs** and **Jobs** in the sidebar
   let you upload a CV (PDF/DOCX) or a job offer (PDF/DOCX/pasted text)
   and see it turn into a structured, evidence-backed profile.

### Running services individually (without Docker)

Useful for fast iteration on just one side. Backend and worker need a
Postgres/Redis reachable at `localhost` - either run `docker compose up
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
Django, CORS, and the frontend's `API_BASE_URL`). `OPENAI_API_KEY` and
`EMBEDDING_MODEL` are now used (Phase 3) - see
[docs/architecture/phase-3-semantics.md](docs/architecture/phase-3-semantics.md);
leaving `OPENAI_API_KEY` unset is fully supported and falls back to a
deterministic local embedding provider. `GEMINI_API_KEY`, `S3_*` remain
documented but unused for later phases.

## Running tests

```bash
make test            # both projects
make test-backend    # pytest, SQLite in-memory - no services required
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
needed for local live-reload - the Makefile always merges both files.

## API

All endpoints are under `/api/v1/`. `cvs/` and `jobs/` follow the same
shape (`document_type` scoped):

| Method | Path                        | Does                                                        |
|--------|-----------------------------|--------------------------------------------------------------|
| GET    | `/api/v1/health/`           | Liveness check                                                |
| POST   | `/api/v1/cvs/`              | Upload a CV (multipart `file`); `202` + queues processing     |
| GET    | `/api/v1/cvs/`              | List uploaded CVs                                             |
| GET    | `/api/v1/cvs/{id}/`         | CV document metadata                                          |
| GET    | `/api/v1/cvs/{id}/status/`  | Processing status + error (if failed)                         |
| GET    | `/api/v1/cvs/{id}/profile/` | Structured `CandidateProfile` (`null` until `PROCESSED`)       |
| POST   | `/api/v1/jobs/`             | Add a job offer (multipart `file`, or JSON `{"text": "..."}`)  |
| GET    | `/api/v1/jobs/`             | List job offers                                                |
| GET    | `/api/v1/jobs/{id}/`        | Job document metadata                                          |
| GET    | `/api/v1/jobs/{id}/status/` | Processing status + error (if failed)                          |
| GET    | `/api/v1/jobs/{id}/profile/`| Structured `JobProfile` (`null` until `PROCESSED`, now includes Phase 3 fields - see below) |
| GET    | `/api/v1/skills/`           | The full skill taxonomy (category, domain, ecosystem, description) |
| GET    | `/api/v1/skills/{canonical_name}/` | One skill's relationships (parent, children, ecosystem siblings, explicit relations) |

`CandidateProfile`/`JobProfile` responses carry Phase 3's normalized
fields alongside the Phase 2 raw ones: `Experience.seniority`,
`Education.degree_level`, `Language.canonical_name`/
`proficiency_normalized`, `JobProfile.seniority_normalized`,
`JobRequirement.minimum_years`/`normalized_value`.

No matching/scoring endpoint exists - see [Known limitations](#known-limitations).
See [docs/api/README.md](docs/api/README.md),
[docs/architecture/phase-2-pipeline.md](docs/architecture/phase-2-pipeline.md),
and [docs/architecture/phase-3-semantics.md](docs/architecture/phase-3-semantics.md)
for the full pipeline and response shapes.

## Backend

Django + Django REST Framework, organized as a modular monolith:

- `config/` - settings (`base` / `development` / `testing` / `production`), root URLs, WSGI/ASGI, and `container.py` (the composition root - see the dependency-rule doc).
- `apps/` - Django app configs + persistence models. `documents` (Document, Evidence), `candidates` (CandidateProfile + parts, now with Phase 3 normalized fields), `jobs` (JobProfile, JobRequirement, same extension), `skills` (Skill, SkillAlias, SkillRelation, seeded taxonomy), and `semantics` (SemanticRepresentation) are implemented; `users`, `analyses`, `recommendations`, `tailoring`, `audit` remain boundaries for later phases.
- `domain/`, `application/`, `infrastructure/`, `interfaces/` - the Clean Architecture layers; see the dependency-rule doc linked above and each layer's own `README.md` for what is implemented vs. reserved.
- `workers/` - Celery app, an infrastructure smoke-test task (`ping`), and `process_cv_document`/`process_job_document` (the real document processing pipeline, now including Phase 3 enrichment/embedding).
- `tests/` - pytest suite (`api/`, `unit/`, `integration/`) plus `tests/fixtures/` (synthetic CV/job fixtures used by parser and extraction tests).

## Frontend

Angular 19, standalone components, feature-based architecture:

- `core/` - app-wide infrastructure: `config` (typed `APP_CONFIG`, backed by `src/environments/`), `http` (`ApiClientService` + auth/error/loading interceptors), `auth` (models/store/service/guard - **not implemented**, see Known limitations), `services` (notification, file-upload, download).
- `shared/` - reusable, feature-agnostic UI: `status-badge`, `evidence-note`, `skill-chip` (now with a lazily-loaded related-skills panel), `entity-tag`, `upload-dropzone`, `processing-timeline`, `toast-stack` (renders `NotificationService`'s state), plus `pollUntilDone` (the status-polling utility) and `formatEnumLabel` (shared enum-to-label formatting).
- `core/icons.ts` - the single registered icon set (Lucide, via `@ng-icons`), provided once at the app root.
- `layout/` - `MainLayoutComponent` (header + sidebar + router-outlet + footer, responsive down to mobile) used by every route; `AuthLayoutComponent` reserved for future login/signup pages.
- `features/cvs`, `features/jobs` - upload workspace (`cv-list`/`job-list`) and detail page (`cv-detail`/`job-detail`) that polls status and renders the structured profile view once processed, including Phase 3's seniority/education/language/requirement enrichment. Real, working features - not placeholders.
- `features/skills` - the skill taxonomy API client and the related-skills panel used from `skill-chip`.
- `features/dashboard` - a real workspace (recent CVs, recent job offers, processing counts, skill taxonomy landscape) plus the Phase 1 health-check widget.
- `features/analysis`, `recommendations`, `tailoring`, `applications`, `settings` - still placeholder pages (later phases).
- `styles/` - the design system: tokens (`_tokens.scss`), typography (`_typography.scss`), and shared mixins (`_mixins.scss`). See [Design system](#design-system).

## Celery

`workers/celery_app.py` configures Celery from Django settings
(`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`, both derived from
`REDIS_URL`). `workers/tasks/infrastructure_tasks.py` defines `ping`
(proves the Django -> Celery -> Redis -> worker path works).
`workers/tasks/document_tasks.py` defines the real pipeline tasks. See
[backend/workers/README.md](backend/workers/README.md).

## Design system

The frontend uses a bespoke design language (Angular has no equivalent
to Tailwind/shadcn in this stack) rather than a generic dashboard
aesthetic: a serif display face (Newsreader) for headings paired with a
humanist sans (IBM Plex Sans) for UI text and a mono (IBM Plex Mono) for
data/evidence, one accent color (terracotta) used consistently, mostly-sharp
surfaces with pill shapes reserved for status/skill chips, and layout
variety (an editorial document view for profiles, a split upload
workspace, a processing timeline) instead of repeating a card-grid
pattern. Status colors (document processing state) are kept separate
from and never reused as skill/requirement match indicators, since no
matching engine exists yet. See `frontend/src/styles/_tokens.scss` for
the full token set.

Phase 3 added a single icon family (Lucide, via `@ng-icons`, registered
once in `core/icons.ts`) used for navigation, section headers, document
types, skills, and status - never emoji, never a mixed set. Skill chips
gained a lazily-loaded related-skills panel (network icon, fetched only
on click), and normalized values (seniority, education level, language
proficiency) render through one shared `entity-tag` primitive.

## Development guidelines

- Follow the dependency rule: `interfaces -> application -> domain`, with
  `infrastructure` implementing abstractions those layers define via
  duck-typed constructor parameters, wired together only in
  `config/container.py` (the composition root). `domain/` must never
  import Django, DRF, Celery, or a vendor SDK.
- Feature code (frontend or backend) must go through `core/`
  (`ApiClientService`, `APP_CONFIG`) rather than hardcoding URLs.
- New Django apps/domain modules should follow the existing folder
  conventions - see [docs/development/getting-started.md](docs/development/getting-started.md).
- No fake functionality: unimplemented features are represented honestly
  (a placeholder page, a "not implemented" error) rather than mocked data.
  Confidence values on extracted facts mean extraction confidence, never
  a claim about the underlying fact - see
  [docs/architecture/phase-2-pipeline.md](docs/architecture/phase-2-pipeline.md).

## Known limitations

- **Authentication is not implemented.** `core/auth/` exists as a
  structural placeholder (`AuthService.login()` always throws,
  `authGuard` always allows navigation) so later phases can wire in real
  auth without moving files. On the backend, `Document.owner` is
  nullable and any document's UUID is enough to read its status/profile
  - a deliberate, temporary development-only assumption (see
  [docs/architecture/phase-2-pipeline.md](docs/architecture/phase-2-pipeline.md)
  "Security baseline"), not a production access model.
- **The document extractors are a rule-based v1**, not a general
  CV/job parser - see phase-2-pipeline.md "Known limitations" for the
  specific boundaries (entry splitting, title/company parsing, English-
  oriented section headings). The `CandidateExtractor`/`JobExtractor`
  abstraction exists so a smarter (or LLM-assisted) extractor can replace
  it later without touching `application/` or `interfaces/`.
- **No candidate-job matching, scoring, recommendations, or tailoring.**
  Phases 2 and 3 deliberately stop at structured, evidence-backed, and
  now semantically enriched profiles - see [Roadmap](#roadmap).
- **Seniority/education/language normalization are keyword tables, not
  an NLP classifier** - the same "rule-based v1" boundary Phase 2
  documented for extraction, applied to Phase 3's normalization. See
  [docs/architecture/phase-3-semantics.md](docs/architecture/phase-3-semantics.md)
  "Known limitations".
- **Embeddings are stored as JSON, not indexed** - `FakeEmbeddingProvider`
  is the default (no network, no API key); `OpenAIEmbeddingProvider`
  activates only when `OPENAI_API_KEY` is configured. No similarity
  search exists yet - see
  [ADR 0002](docs/adr/0002-json-embeddings-not-pgvector.md).
- **No ESLint configuration for the frontend** - Angular 19's `ng new` no
  longer scaffolds one by default. `make lint-frontend` runs TypeScript's
  type-checker instead; adding ESLint is left for when the team defines a
  house style, rather than adopting Angular CLI's defaults speculatively.
- **`black --check` fails in this environment** on Python 3.12.5 due to a
  [known CPython AST safety issue](https://github.com/psf/black) that
  Black refuses to run under; it works on 3.12.6+ or 3.12.4-. `ruff check`
  (the more substantial static-analysis pass) is unaffected and passes.
- **No production Dockerfile/compose** - `infrastructure/docker/*.Dockerfile`
  and `docker-compose*.yml` are development-only (dev servers, bind
  mounts). `config/settings/production.py` exists for a future deployment
  but isn't exercised by anything in this repository yet.
- **Storage is local-filesystem only** - `infrastructure/storage/local.py`
  is the only `FileStorage` implementation. An `S3Storage` can be added
  later behind the same abstraction without changing any caller.

## Roadmap

- **Phase 4** - the ATS Matching Engine: candidate-job matching over the
  semantic representations Phase 3 produced, evidence retrieval, and
  (if justified once real query volume exists) indexed vector search.
- **Phase 5** - deterministic, explainable scoring engine, gap analysis,
  recommendations.
- **Phase 6** - LLM-assisted explanations, CV tailoring, and claim
  validation ("truth layer").
