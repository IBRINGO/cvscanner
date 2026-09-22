# domain/

The intellectual core of CVScanner: business entities, value objects, and
rules for parsing, matching, scoring, and recommending. See
[dependency-rule.md](../../docs/architecture/dependency-rule.md) — code in
this package must never import Django, DRF, Celery, or a vendor SDK.

Nothing here is implemented yet beyond the package boundaries; Phase 1 only
reserves the following modules for the phases that build the ATS
Intelligence Engine:

| Module            | Will eventually hold                                          | Phase |
|--------------------|----------------------------------------------------------------|-------|
| `cv/`              | `CV` entity, value objects, parsing-result policies             | 2     |
| `candidate/`       | `CandidateProfile` entity extracted from a CV                   | 2     |
| `job/`             | `JobProfile` entity and `Requirement` value objects              | 2     |
| `skills/`          | Skill taxonomy, normalization, relationships                     | 2     |
| `matching/`        | `MatchResult`, `Evidence`, matching strategies                   | 3     |
| `scoring/`         | Deterministic, explainable ATS score calculation                 | 4     |
| `recommendations/` | Recommendation entities and prioritization rules                 | 4     |
| `tailoring/`       | `TailoredCV` entity, tailoring/validation policies                | 5     |
