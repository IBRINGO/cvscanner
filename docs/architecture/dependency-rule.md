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
   through abstractions (e.g. a repository interface, an `LLMProvider`
   interface) — never a concrete vendor class.
3. `infrastructure/*` implements those abstractions (Postgres repositories,
   PDF/DOCX parsers, OpenAI/Gemini providers, S3 storage, Redis cache). It is
   the only layer allowed to import vendor SDKs and Django's ORM.
4. `interfaces/api/*` (Django views/serializers/urls) depends on
   `application/*` use cases. Views should stay thin: parse input, call a use
   case, serialize output.
5. `apps/*` contains Django app configuration and persistence models. Models
   are infrastructure, not domain entities — do not let a serializer or view
   reach into `domain/` internals and treat a Django model as if it were the
   business entity.

## Why this matters for CVScanner specifically

The ATS Intelligence Engine (matching, scoring, recommendations, tailoring)
is the core intellectual property of this product. Keeping it framework-free
means:

* it can be unit-tested without a database or an HTTP server;
* the LLM vendor (OpenAI, Gemini, a local model) can change without touching
  business rules;
* the scoring/matching logic can be extracted into its own service later
  without a rewrite, because it never depended on Django in the first place.
