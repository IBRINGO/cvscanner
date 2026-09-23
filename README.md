# CVScanner

CVScanner is an intelligent ATS (Applicant Tracking System) analysis
platform. A user uploads a CV and a job offer; the platform parses both,
extracts structured information, matches the candidate against the job's
requirements, produces an explainable score, and recommends improvements
(including, eventually, a tailored CV with claims validated against
evidence).

**This repository's backend is at Phase 5 (Evidence-Backed Recommendations
and CV Tailoring); the frontend has completed Phase 6, a full product
redesign on top of that same backend.** CVs and job offers can be
uploaded, parsed, and structured into evidence-backed profiles with
normalized skills (Phase 2), enriched with skill relationships and
normalized seniority/education/language (Phase 3), and matched against a
job through a hybrid lexical/alias/ontology/semantic engine with a
deterministic, versioned score and structured gaps (Phase 4). Phase 5
turns those gaps into deterministic, evidence-backed recommendations, and
lets a candidate generate a tailored CV - reordering, normalizing, and
(optionally) LLM-assisted rephrasing - with every generated claim
independently checked by a Truth Layer before it can appear, and the
tailored result re-scored through the same Phase 4 engine. Nothing
outside a candidate's verified experience is ever added.

Phase 6 rebuilt the Angular frontend around that capability as a real
CV -> Job -> Analysis -> Recommendations -> Tailoring -> Export
application journey instead of an admin dashboard: a derived
"Applications" workspace home, an animated ATS score gauge, a document-
centric guided upload flow, a six-template CV editor with live preview,
and PDF export - all on the exact same API contracts above, no backend
change. See [docs/architecture/phase-6-frontend-redesign.md](docs/architecture/phase-6-frontend-redesign.md).
See [Roadmap](#roadmap) and [Known limitations](#known-limitations) for
what is deliberately still out of scope (recommendations beyond text,
cover letters, CV rewriting beyond wording, ranking, DOCX export).

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
| POST   | `/api/v1/analyses/`         | Create an ATS analysis for a processed CV + job offer pair; queues matching |
| GET    | `/api/v1/analyses/`         | List analyses |
| GET    | `/api/v1/analyses/{id}/`    | Full analysis: score breakdown, requirement evaluations, gaps |
| GET    | `/api/v1/analyses/{id}/status/` | Processing status + error (if failed) |
| GET    | `/api/v1/analyses/{id}/recommendations/` | Deterministic, evidence-backed recommendations for a completed analysis |
| POST   | `/api/v1/tailoring/`        | Create a tailoring plan for selected recommendations; queues generation |
| GET    | `/api/v1/tailoring/`        | List tailoring plans |
| GET    | `/api/v1/tailoring/{id}/`   | Full plan: operations, before/after scores, requirement deltas, changes |
| GET    | `/api/v1/tailoring/{id}/status/` | Processing status + error (if failed) |
| GET    | `/api/v1/tailoring/{id}/changes/` | The tailored changes and their diffs only |

`CandidateProfile`/`JobProfile` responses carry Phase 3's normalized
fields alongside the Phase 2 raw ones: `Experience.seniority`,
`Education.degree_level`, `Language.canonical_name`/
`proficiency_normalized`, `JobProfile.seniority_normalized`,
`JobRequirement.minimum_years`/`normalized_value`.

See [docs/api/README.md](docs/api/README.md),
[docs/architecture/phase-2-pipeline.md](docs/architecture/phase-2-pipeline.md),
[docs/architecture/phase-3-semantics.md](docs/architecture/phase-3-semantics.md),
[docs/architecture/phase-4-matching.md](docs/architecture/phase-4-matching.md),
and [docs/architecture/phase-5-recommendations-and-tailoring.md](docs/architecture/phase-5-recommendations-and-tailoring.md)
for the full pipeline and response shapes.

## Backend

Django + Django REST Framework, organized as a modular monolith:

- `config/` - settings (`base` / `development` / `testing` / `production`), root URLs, WSGI/ASGI, and `container.py` (the composition root - see the dependency-rule doc).
- `apps/` - Django app configs + persistence models. `documents` (Document, Evidence), `candidates` (CandidateProfile + parts, now with Phase 3 normalized fields), `jobs` (JobProfile, JobRequirement, same extension), `skills` (Skill, SkillAlias, SkillRelation, seeded taxonomy), `semantics` (SemanticRepresentation), `analyses` (Analysis, RequirementEvaluationRecord - Phase 4), `recommendations` (Recommendation - Phase 5), and `tailoring` (TailoringPlan, TailoringChange - Phase 5) are implemented; `users`, `audit` remain boundaries for later phases.
- `domain/`, `application/`, `infrastructure/`, `interfaces/` - the Clean Architecture layers; see the dependency-rule doc linked above and each layer's own `README.md` for what is implemented vs. reserved. `domain/matching/` (Phase 4) is the hybrid matching engine itself; `domain/truth/` (Phase 5) is the factual-safety layer every generated CV claim passes through; `domain/tailoring/` (Phase 5) is the tailoring plan/diff model - all pure Python, no framework imports.
- `workers/` - Celery app, an infrastructure smoke-test task (`ping`), `process_cv_document`/`process_job_document` (the document processing pipeline), `run_analysis` (Phase 4's matching task), and `run_tailoring` (Phase 5's generation/validation/re-analysis task).
- `tests/` - pytest suite (`api/`, `unit/`, `integration/`) plus `tests/fixtures/` (synthetic CV/job fixtures used by parser and extraction tests).

## Frontend

Angular 19, standalone components, feature-based architecture. See
[docs/architecture/phase-6-frontend-redesign.md](docs/architecture/phase-6-frontend-redesign.md)
for the full redesign rationale.

- `core/` - app-wide infrastructure: `config` (typed `APP_CONFIG`, backed by `src/environments/`), `http` (`ApiClientService` + auth/error/loading interceptors), `auth` (models/store/service/guard - **not implemented**, see Known limitations), `services` (notification, file-upload, download).
- `shared/` - reusable, feature-agnostic UI: `status-badge`, `evidence-note`, `skill-chip` (with a lazily-loaded related-skills panel), `entity-tag`, `upload-dropzone`, `processing-timeline`, `toast-stack`, plus the Phase 6 primitives `score-gauge` (the animated ATS score visualization), `application-progress` (the CV -> Export journey step indicator), and `document-preview` (paper-styled document previews); `pollUntilDone` (status polling) and `formatEnumLabel` (enum-to-label formatting).
- `core/icons.ts` - the single registered icon set (Lucide, via `@ng-icons`), provided once at the app root.
- `layout/` - `MainLayoutComponent` (header + sidebar + router-outlet + footer, responsive down to mobile) used by every route; `AuthLayoutComponent` reserved for future login/signup pages.
- `features/cvs`, `features/jobs` - the library pages (`cv-list`/`job-list`) and detail pages (`cv-detail`/`job-detail`) for uploading/reviewing CVs and job offers independently of the guided journey below, plus (Phase 6) `cv-editor` - the structured, client-side-only CV editor at `/cvs/:id/editor` (see [ADR 0005](docs/adr/0005-cv-editor-stays-client-side.md)).
- `features/skills` - the skill taxonomy API client and the related-skills panel used from `skill-chip`.
- `features/workspace` (Phase 6, replaces the old `dashboard`) - the product home: real Active Applications first, an "Analyze a new application" entry point, then recent CVs/jobs and the skill-taxonomy landscape. No KPI cards.
- `features/applications` (Phase 6, real - no longer a placeholder) - `build-applications.ts` derives the Applications view client-side from CVs/jobs/analyses/tailoring plans (no new backend entity); `new-application` is the guided CV -> Job -> Analysis journey at `/applications/new`; `application-list` is the full index.
- `features/analysis` - the ATS analysis workspace (Phase 4, Phase 6 visuals): a candidate/job picker and history list (`analysis-list`), and the analysis detail page with an animated `ScoreGauge`, a What-is-working/What-needs-attention strengths-and-weaknesses split, an expandable requirement matrix with per-row confidence and an evidence explorer, and the journey progress indicator.
- `features/recommendations` - the recommendations workspace for one analysis (Phase 5, Phase 6 visuals): findings grouped by priority with explicit Why/Evidence/Recommended-action fields, a safety badge on every row, a selection checkbox only where CVScanner can act safely, and the entry point into tailoring.
- `features/tailoring` - the tailored-CV workspace (Phase 5, Phase 6 visuals): an honest progress timeline, before/after `ScoreGauge`s (identical when tailoring did not move the score - never implying an improvement that didn't happen), a factual-consistency summary, and every change shown as a paper-styled document card with its diff - accepted or rejected, never hidden.
- `features/templates` (new, Phase 6) - `cv-document-renderer`, the one data-driven component rendering a `CandidateProfile` through six ATS-friendly templates via CSS variation only; `template-gallery` (`/templates`) previews all six at full size.
- `settings` - still a placeholder page (later phase).
- `styles/` - the design system: tokens (`_tokens.scss`), typography (`_typography.scss`), and shared mixins (`_mixins.scss`). See [Design system](#design-system).

## Celery

`workers/celery_app.py` configures Celery from Django settings
(`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`, both derived from
`REDIS_URL`). `workers/tasks/infrastructure_tasks.py` defines `ping`
(proves the Django -> Celery -> Redis -> worker path works).
`workers/tasks/document_tasks.py` defines the real pipeline tasks. See
[backend/workers/README.md](backend/workers/README.md).

## Design system

Phase 6 replaced the frontend's visual identity outright rather than
extending the prior one: a document-first, precision/measurement register
instead of an editorial reading register. Headings, scores, and document
titles use Space Grotesk (a confident geometric grotesk); UI text stays
IBM Plex Sans and data/evidence stays IBM Plex Mono. One brand accent
(a deep signal blue) drives every primary action and "actively
processing" state; a decoupled semantic palette
(`--positive`/`--attention`/`--negative`/`--inferred`, aliased for call-site
clarity as `--match-*` and `--status-*`) means a color always means the
same thing everywhere, and the brand accent never doubles as a warning
color the way the prior terracotta accent did. CV/job documents render
onto a distinct "paper" surface family (`--paper-surface`, `--paper-border`,
`--paper-ink`, `--shadow-document`) that stays paper-like even in dark
mode, so a document always reads as a real document rather than another
UI panel. Mostly-sharp surfaces, pill shapes reserved for chips, and
layout variety (a derived-applications workspace, a guided document
upload journey, an animated score gauge, a live CV editor with template
switching) instead of a repeating card-grid dashboard pattern. See
`frontend/src/styles/_tokens.scss` for the full token set and
[docs/architecture/phase-6-frontend-redesign.md](docs/architecture/phase-6-frontend-redesign.md)
for the full rationale.

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
- **Tailoring only rewrites `SKILL` and `EXPERIENCE` facts** - the two
  fact types the current recommendation types
  (`KEYWORD_PLACEMENT`/`RESPONSIBILITY_ALIGNMENT`) ever mark safe to
  automate. Reordering sections and every other recommendation type stay
  informational, acted on by the candidate manually - see
  [docs/architecture/phase-5-recommendations-and-tailoring.md](docs/architecture/phase-5-recommendations-and-tailoring.md)
  "Known limitations".
- **No cover letters, interview prep, or candidate ranking.** Phase 5
  stops at recommending and tailoring wording for one candidate against
  one job - see [Roadmap](#roadmap).
- **Seniority/education/language normalization are keyword tables, not
  an NLP classifier** - the same "rule-based v1" boundary Phase 2
  documented for extraction, applied to Phase 3's normalization. See
  [docs/architecture/phase-3-semantics.md](docs/architecture/phase-3-semantics.md)
  "Known limitations".
- **Embeddings are stored as JSON, not indexed** - `FakeEmbeddingProvider`
  is the default in tests (no network, no API key); `GeminiEmbeddingProvider`
  is the primary provider when `GEMINI_API_KEY` is configured, with
  `OpenAIEmbeddingProvider` as a fallback when `OPENAI_API_KEY` is
  configured. If every configured provider fails, matching degrades to
  lexical/ontology signals only rather than failing the analysis. No
  similarity search exists yet - see
  [ADR 0002](docs/adr/0002-json-embeddings-not-pgvector.md).
- **The matching engine is a rule-based hybrid, not an ML ranker.**
  Semantic similarity is one signal among several and is only consulted
  when lexical/alias/ontology matching does not resolve a requirement -
  see [ADR 0003](docs/adr/0003-hybrid-matching-not-pure-embeddings.md)
  and [docs/architecture/phase-4-matching.md](docs/architecture/phase-4-matching.md)
  "Known limitations" for the specific boundaries (experience-date
  parsing, responsibility matching's lightweight lexical/semantic
  overlap, certifications never inferred from skills).
- **Generated CV wording is never trusted on its own.** Every proposed
  change - deterministic or LLM-assisted - passes through an
  independent, deterministic Truth Layer before it can appear; a
  provider failure or a rejected claim falls back to the original text,
  never a crash and never invented filler. See
  [ADR 0004](docs/adr/0004-truth-layer-independent-claim-validation.md).
- **DOCX export is not implemented.** The CV editor exports PDF via a
  scoped print stylesheet (no new dependency, exact template fidelity).
  DOCX would need either a new client-side library or backend work and
  was deliberately deferred rather than shipped as a non-functional
  button - see
  [docs/architecture/phase-6-frontend-redesign.md](docs/architecture/phase-6-frontend-redesign.md).
- **CV editor edits are client-side only and are not saved anywhere.**
  Reordering sections, hiding sections, rewording text, and removing
  entries all happen in-memory and feed only the live preview and PDF
  export; refreshing or navigating away loses in-progress edits, and
  nothing written there can ever reach the Truth Layer's "verified
  candidate fact" data - see
  [ADR 0005](docs/adr/0005-cv-editor-stays-client-side.md).
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

- **Phase 7** - DOCX export, persisted CV editor versions (a
  deliberately separate data model from `CandidateProfile` - see
  [ADR 0005](docs/adr/0005-cv-editor-stays-client-side.md)), cover
  letter generation, richer document-level tailoring (section
  reordering, summary rewriting), and claim validation for content
  types beyond the five categories `domain/truth/` currently checks.
