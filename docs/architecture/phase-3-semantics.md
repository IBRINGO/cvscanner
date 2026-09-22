# Phase 3 - Semantic Intelligence and Knowledge Enrichment

This document describes what Phase 3 actually built on top of Phase 2's
document intelligence pipeline (see
[phase-2-pipeline.md](phase-2-pipeline.md)). Phase 2 answers "what
information is present in this document?"; Phase 3 answers "what does
that information mean, and how is it related?" Nothing in Phase 3
compares a candidate to a job or produces a score - see "Phase 4
boundary" at the end.

## The enrichment stage

```text
Phase 2 pipeline (unchanged)
        v
CandidateProfile / JobProfile persisted, with Evidence
        v
Semantic enrichment (Phase 3, new)          -- application/semantics/
   - seniority normalization                   enrich_candidate_profile.py
   - education level normalization              enrich_job_profile.py
   - language normalization
   - technology mentions scanned from prose   -- domain/skills/enrichment.py
   - experience requirement parsing            domain/job/requirement_semantics.py
        v
Optional embedding generation                -- application/semantics/
   - degrades silently on provider failure       generate_embeddings.py
```

`ProcessCvDocumentPipeline`/`ProcessJobDocumentPipeline`
(`application/cv/process_pipeline.py`,
`application/jobs/process_pipeline.py`) call the enrichment and
embedding use cases immediately after Phase 2 extraction succeeds, in
the same Celery task. Both steps are wrapped in their own `try/except`:
a failure in enrichment or embedding generation is logged and skipped,
never allowed to mark an otherwise-successful document as `FAILED` -
Phase 2's facts are already committed by that point and stay valid
either way (sections 62/80 of the brief).

## Skill taxonomy and relationships

`domain/skills/entities.py::Skill` gained `ecosystem`, `description`,
and `relations` (a tuple of typed `SkillRelation` edges). Three of the
six relationship types in `domain/skills/enums.py::SkillRelationType`
are never stored - they are derived at read time by
`domain/skills/relationships.py::build_relationship_view`:

* `PARENT_OF` / `CHILD_OF` - derived from `Skill.parent_skill`.
* `PART_OF_ECOSYSTEM` - derived from two skills sharing the same
  `Skill.ecosystem` string.

Only `RELATED_TO`, `ALTERNATIVE_TO`, and `BUILDS_ON` are stored
explicitly, in `apps/skills/models.py::SkillRelation`, because they are
genuinely editorial judgments (e.g. "Flask is an alternative to
Django") that cannot be derived from category/ecosystem alone. This
follows section 8 of the brief directly: "do not make all relationships
bidirectional manually if the data model can derive them."

None of this ever asserts two skills are the same thing - see
`domain/skills/normalization.py`'s existing module docstring, unchanged
since Phase 2. `Django REST Framework`'s parent is `Django`; `Django`'s
parent is `Python`; none of the three normalize to each other.

**Technology mention scanning** (`domain/skills/enrichment.py::
TechnologyMentionScanner`) is the concrete answer to section 13: Phase 2
only reads skills from a dedicated Skills section. Phase 3 additionally
scans each experience's `description`/`achievements` text against the
full taxonomy (longest surface form first, custom word-boundary regex
that handles `C++`/`C#`/`.NET` correctly) and merges any matches into
that experience's `technologies` list, alongside whatever an explicit
"Technologies:" line already provided. A skill not in the taxonomy is
simply not found - never guessed.

## Normalization modules

Three new, deterministic, framework-free modules, mirroring the
Phase 2 principle of explainable keyword/regex matching over invented
inference:

* `domain/cv/seniority.py::normalize_seniority` - a controlled
  `SeniorityLevel` vocabulary (`INTERN` through `EXECUTIVE`, plus
  `UNKNOWN`). Matches explicit keywords in a title only; a title with no
  seniority keyword ("Software Engineer") normalizes to `UNKNOWN`, never
  a guessed `MID`.
* `domain/cv/education_normalization.py::normalize_education_level` - a
  controlled `EducationLevel` vocabulary from the raw degree string.
* `domain/cv/language_normalization.py` - `normalize_language_name`
  (a small curated table of English/French surface forms to a canonical
  English name) and `normalize_proficiency` (CEFR codes and common
  words to a controlled `LanguageProficiency` vocabulary).
* `domain/job/requirement_semantics.py::parse_experience_requirement` -
  extracts `minimum_years` and, if a known skill is named in the same
  sentence, `technology`, from an already-classified `EXPERIENCE`
  requirement's raw text. Ambiguous text keeps `minimum_years = None`
  rather than inventing a number.

Every normalized value is stored **alongside** the raw value it was
computed from (`Experience.seniority` next to `Experience.title`,
`Education.degree_level` next to `Education.degree`,
`Language.canonical_name`/`proficiency_normalized` next to
`Language.name`/`proficiency`, `JobRequirement.minimum_years`/
`normalized_value` next to `JobRequirement.raw_text`) - the raw text is
never replaced, per section 11/16/17 of the brief.

## Semantic representation and embeddings

`domain/semantics/entities.py::SemanticRepresentation` is a small,
framework-free record: which entity was embedded, what text was
embedded, the resulting vector, and which model/version produced it.
`infrastructure/embeddings/base.py::EmbeddingProvider` is the Protocol
the domain depends on; two implementations exist:

* `FakeEmbeddingProvider` - deterministic (SHA-256-derived), no network
  call, explicitly documented as having no real semantic meaning. This
  is what development and every automated test use.
* `OpenAIEmbeddingProvider` - a real implementation using a plain HTTPS
  POST (not the `openai` SDK, to keep the dependency small), used only
  when `OPENAI_API_KEY` is configured.

`config/container.py::build_embedding_provider` picks between them
based on whether `settings.OPENAI_API_KEY` is set - the domain and
application layers never know which one is active. `config/settings/
testing.py` forces this empty so the test suite never depends on a live
network call or a real API key, even if a developer's local `.env`
defines one.

Embeddings are stored as a JSON float array
(`apps/semantics/models.py::SemanticRepresentation`), not `pgvector` -
see [ADR 0002](../adr/0002-json-embeddings-not-pgvector.md) for why.

## API surface

The existing `.../profile/` endpoints for CVs and jobs now include the
Phase 3 fields directly (no new "intelligence" endpoint was needed -
these are the same resources, with more fields). A new read-only
resource was added for the taxonomy itself:

* `GET /api/v1/skills/` - every skill, with its category/domain and
  description.
* `GET /api/v1/skills/{canonical_name}/` - one skill's full relationship
  view (parent, children, ecosystem siblings, explicit relations).

## Known limitations (Phase 3 v1)

* Technology-mention scanning is alias-based only; a skill spelled in a
  way not covered by the taxonomy's aliases is not found in prose (same
  boundary Phase 2 documented for the Skills section itself).
* Seniority/education/language normalization are English/French-biased
  keyword tables, not a general NLP classifier - the same "rule-based
  v1, not a general parser" boundary Phase 2 already documented for
  extraction.
* `minimum_years` parsing only handles the common "N years" / "N+
  years" phrasing; a requirement phrased unusually keeps `raw_text` with
  `minimum_years = None`.
* Embeddings are generated once per document (a single consolidated
  text per CandidateProfile/JobProfile), not per experience or per
  requirement - proportional to what a foundation needs (section 66:
  avoid embedding every small string individually), not a full
  per-fact embedding index.
