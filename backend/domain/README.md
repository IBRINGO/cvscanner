# domain/

The intellectual core of CVScanner: business entities, value objects, and
rules for parsing, matching, scoring, and recommending. See
[dependency-rule.md](../../docs/architecture/dependency-rule.md) - code in
this package must never import Django, DRF, Celery, or a vendor SDK.

| Module              | Holds                                                                 | Status (Phase) |
|---------------------|------------------------------------------------------------------------|----------------|
| `documents/`        | `Document`/`ParsedDocument` lifecycle, `Evidence`, validation policies  | Implemented (2)|
| `cv/`               | `CandidateProfile` and its parts (Experience, Education, ...), section detection | Implemented (2)|
| `job/`              | `JobProfile`, `JobRequirement`                                          | Implemented (2)|
| `skills/`           | Skill taxonomy, normalization, ecosystem/relationship derivation (`relationships.py`), technology-mention scanning (`enrichment.py`) | Implemented (2, enriched 3) |
| `semantics/`        | `SemanticRepresentation`, `SemanticEntityType`                          | Implemented (3)|
| `matching/`         | `MatchResult`, matching strategies                                      | Phase 4        |
| `scoring/`          | Deterministic, explainable ATS score calculation                       | Phase 5        |
| `recommendations/`  | Recommendation entities and prioritization rules                       | Phase 5        |
| `tailoring/`        | `TailoredCV` entity, tailoring/validation policies                     | Phase 6        |

Phase 3 also added `cv/seniority.py`, `cv/education_normalization.py`,
`cv/language_normalization.py`, and `job/requirement_semantics.py` to
the existing `cv/`/`job/` modules - see
[docs/architecture/phase-3-semantics.md](../../docs/architecture/phase-3-semantics.md).

## A Phase 1 plan deviation, documented

Phase 1 reserved a separate `candidate/` module for the future
`CandidateProfile` entity. Phase 2 puts `CandidateProfile` in `cv/`
instead (`domain/cv/entities.py`) and leaves `candidate/` empty.

**Why:** in this codebase, a `CandidateProfile` only ever exists as the
parsed structure of exactly one CV (a strict 1:1 relationship - see
`apps/candidates/models.py::CandidateProfile.document`). Splitting the
entity into a separate `candidate/` module would have meant `cv/` and
`candidate/` constantly importing each other's types (`Experience`,
`Education`, ... all belong conceptually to "what a CV contains") for no
architectural benefit. `candidate/` is kept as an empty, reserved
package rather than deleted, in case a future phase introduces a
candidate identity that outlives any single CV (e.g. merging multiple
CVs into one profile) - at that point splitting the module would earn
its keep.

## documents/ vs cv/job/skills/

`documents/` is new in Phase 2 and not something Phase 1 anticipated by
name - see its own docstring for why "a document being ingested and
parsed" needed to be modeled separately from "a CV" or "a job offer" (both
are Documents first, before they become a structured profile).
