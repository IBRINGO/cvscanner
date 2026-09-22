# CVScanner — Architecture Overview

## What CVScanner is

CVScanner is an intelligent ATS (Applicant Tracking System) analysis platform.
A user uploads a CV and a job offer; the platform will eventually parse both,
extract structured information, match the candidate against the job
requirements, produce an explainable score, and recommend improvements
(including an optional tailored CV).

This document describes the **Phase 1 foundation**. The ATS Intelligence
Engine itself (parsing, matching, scoring, recommendations, tailoring) is
intentionally out of scope for this phase — see [Future Direction](#future-direction).

## System components

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
                              │ (data)     │   │ (broker/  │   │  (worker)  │
                              │            │   │  cache)   │   │            │
                              └───────────┘   └───────────┘   └────────────┘
```

Each component is independently executable and could be deployed on its own
in the future. During local development, Docker Compose orchestrates all of
them together.

## Backend dependency direction

The backend follows a modular Clean Architecture / pragmatic DDD approach.
Dependencies point strictly inward:

```text
             ┌───────────────┐
             │   interfaces  │   REST API (Django views/serializers)
             └───────┬───────┘
                     ▼
             ┌───────────────┐
             │  application  │   Use cases / orchestration
             └───────┬───────┘
                     ▼
             ┌───────────────┐
             │    domain     │   ATS business rules (framework-free)
             └───────────────┘
                     ▲
             ┌───────┴───────┐
             │ infrastructure│   DB repositories, parsers, LLM providers,
             │               │   storage, cache, observability
             └───────────────┘
```

* `interfaces/` depends on `application/`.
* `application/` depends on `domain/` and on infrastructure **abstractions**
  (never concrete vendor SDKs).
* `domain/` depends on nothing outside the Python standard library. It must
  never import Django, DRF, Celery, or any vendor SDK (OpenAI, Gemini, etc.).
* `infrastructure/` implements the abstractions that `domain/`/`application/`
  define, and is the only layer allowed to depend on frameworks and vendor
  SDKs.
* `apps/` holds Django-specific persistence models and wiring. Django models
  are an infrastructure/persistence concern — they are not the domain model.

This boundary is what allows the ATS Intelligence Engine (Phases 2–5) to grow
without ever coupling business rules to Django or a specific LLM vendor.

## Why a modular monolith, not microservices

See [ADR 0001](../adr/0001-modular-monolith-and-monorepo.md) for the full
reasoning. In short: at this stage the team, traffic, and scaling needs do
not justify the operational cost of independent services. The module
boundaries inside the monolith are explicit enough that extraction later
(e.g. a dedicated `matching` or `llm` service) is possible without a rewrite.

## Future direction

Phases 2–5 will build the ATS Intelligence Engine inside the boundaries
established here:

* **Phase 2** — document parsing (PDF/DOCX), structured candidate/job
  profiles, skill normalization.
* **Phase 3** — embeddings, pgvector, hybrid (lexical + semantic) search,
  evidence retrieval.
* **Phase 4** — deterministic, explainable scoring engine and gap analysis.
* **Phase 5** — LLM-assisted explanations/recommendations, CV tailoring, and
  claim validation against evidence (a "truth layer").

None of this is implemented yet. Phase 1 only guarantees the boundaries
(`domain/matching`, `domain/scoring`, `infrastructure/llm`, etc.) exist so
later phases have a home.
