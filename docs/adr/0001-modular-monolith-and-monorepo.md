# ADR 0001: Modular Monolith in a Monorepo

* Status: Accepted
* Date: 2026-09-22

## Context

CVScanner needs a foundation that supports a fairly ambitious long-term
scope (document parsing, embeddings, hybrid search, deterministic scoring,
LLM-assisted recommendations, CV tailoring) while remaining buildable by a
small team starting from zero. We need to decide the repository layout, the
backend runtime architecture, and the core technology choices for Phase 1.

## Decision

### Monorepo

`frontend/`, `backend/`, `docs/`, and `infrastructure/` live in a single
repository.

**Why:** at this stage there is a single team and a single product. A
monorepo keeps local setup, versioning, and cross-cutting changes (e.g.
updating the API contract used by both frontend and backend) simple. It does
not imply a monolithic *runtime* — see below.

### Angular for the frontend

**Why:** strongly-typed, batteries-included framework with first-class
routing, reactive forms, and an HTTP client — a good fit for a data-heavy,
form-heavy ATS product. The team standardizes on Angular 19 (latest stable
release compatible with the available Node.js 20.16 runtime; Angular 20
requires Node ^20.19, which is not yet available in this environment).

### Django + Django REST Framework for the backend

**Why:** Django's ORM, migrations, and admin give us a fast, safe path to a
relational data model, and DRF gives us a mature REST toolkit (serializers,
viewsets, pagination, permissions) without reinventing them. Python is also
the natural choice for the future AI/ML-heavy ATS Intelligence Engine
(document parsing, embeddings, LLM orchestration).

### Modular monolith, not microservices

The backend is a **single deployable Django project** internally organized
into explicit modules (`domain/`, `application/`, `infrastructure/`,
`interfaces/`, and Django `apps/`), with a strict dependency rule (see
[dependency-rule.md](../architecture/dependency-rule.md)).

**Why not microservices now:**

* There is no independent scaling requirement yet — CV parsing, matching,
  and scoring will initially run at low volume.
* Microservices add real operational cost (service discovery, distributed
  tracing, versioned inter-service contracts, multiple deployment
  pipelines) that is not justified before the product itself is validated.
* A modular monolith with explicit boundaries gets us most of the
  organizational benefit (clear ownership of `matching`, `scoring`, `llm`,
  etc.) without the operational cost.

**How extraction stays possible:** because `domain/matching`,
`domain/scoring`, and `infrastructure/llm` never depend on Django internals
directly (only through abstractions consumed by `application/`), any of
these modules can later be lifted into its own service behind the same
interface it already exposes to `application/`, without rewriting business
logic.

### PostgreSQL

**Why:** mature relational database with JSON column support (for flexible
structured extraction results) and, in a later phase, `pgvector` for
embeddings — meaning we do not need a second, separate vector database.

### Redis + Celery

**Why:** CV parsing and (later) LLM calls are I/O-heavy and must not block
HTTP requests. Redis is a simple, well-understood broker/result-backend for
Celery, and doubles as a cache. `celery-beat` is intentionally **not**
included yet — there is no scheduled-task requirement in Phase 1.

## Consequences

* Local development requires five services (frontend, backend, worker,
  postgres, redis), orchestrated by Docker Compose.
* Every new backend module must respect the dependency rule; this is a
  process/code-review responsibility, not something enforced by tooling in
  Phase 1.
* Revisiting this decision (e.g. extracting a service) is expected only once
  a concrete scaling or team-ownership need appears — not preemptively.
