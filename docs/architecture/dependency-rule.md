# Backend Dependency Rule

This document exists so the rule is impossible to miss.

```text
interfaces → application → domain
                              ▲
                              │ (implements abstractions defined here)
                        infrastructure
```

## Rules

1. `domain/*` never imports `django`, `rest_framework`, `celery`, `redis`,
   `openai`, `google.genai`, or any other framework/vendor package. It is
   plain Python: entities, value objects, enums, policies, exceptions.
2. `application/*` orchestrates `domain/*` and depends on infrastructure only
   through abstractions (e.g. a repository, a `FileStorage`, a
   `DocumentParser`, a `CandidateExtractor`) - never a concrete vendor
   class. These abstractions are duck-typed constructor parameters
   (documented via docstrings), not imported Protocol classes - see
   "The composition root" below for why `application/*` never imports
   `infrastructure/*` even to reference a Protocol type.
3. `infrastructure/*` implements those abstractions (Postgres repositories,
   PDF/DOCX parsers, OpenAI/Gemini providers, S3 storage, Redis cache). It is
   the only layer allowed to import vendor SDKs and Django's ORM.
4. `interfaces/api/*` (Django views/serializers/urls) depends on
   `application/*` use cases. Views should stay thin: parse input, call a use
   case, serialize output.
5. `apps/*` contains Django app configuration and persistence models. Models
   are infrastructure, not domain entities - do not let a serializer or view
   reach into `domain/` internals and treat a Django model as if it were the
   business entity.

## The composition root

Something has to import both `application/*` use cases and concrete
`infrastructure/*` implementations to wire them together - that
something is `config/container.py`, and it is the *only* module allowed
to do so. `interfaces/api/*` views and `workers/tasks/*` both call
`config/container.py` factory functions (e.g. `build_cv_processing_pipeline()`)
instead of importing infrastructure classes or constructing use cases
themselves.

This is why `application/*` can depend on abstractions "through duck
typing" rather than importing a Protocol class from `infrastructure/*`:
the concrete object built in `config/container.py` is passed into the
use case's constructor, and Python's structural typing means the use
case never needs to know (or import) the concrete class's module.

## Why this matters for CVScanner specifically

The ATS Intelligence Engine (matching, scoring, recommendations, tailoring)
is the core intellectual property of this product. Keeping it framework-free
means:

* it can be unit-tested without a database or an HTTP server;
* the LLM vendor (OpenAI, Gemini, a local model) can change without touching
  business rules;
* the scoring/matching logic can be extracted into its own service later
  without a rewrite, because it never depended on Django in the first place.
