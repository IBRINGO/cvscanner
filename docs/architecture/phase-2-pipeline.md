# Phase 2 - Document Intelligence Pipeline

This document describes what Phase 2 actually built: turning an uploaded
CV or job offer into structured, evidence-backed data. See
[overview.md](overview.md) and [dependency-rule.md](dependency-rule.md)
for the Phase 1 architecture this builds on; nothing here changes those
rules.

## The pipeline

```text
Raw file (PDF / DOCX / plain text)
        v
Document ingestion (validate, hash, store)          -- application/documents/upload_document.py
        v
Document parsing (extract text, preserve pages)      -- application/documents/parse_document.py
        v                                                infrastructure/document_processing/parsers/
ParsedDocument (raw_text, pages[], blocks[])
        v
Section detection (rule-based heading matching)       -- domain/cv/policies.py::detect_sections
        v
list[DetectedSection]
        v
Structured extraction                                 -- application/cv/extract_candidate_profile.py
   (CandidateProfile or JobProfile,                       application/jobs/extract_job_profile.py
    each fact carrying its own Evidence)                  infrastructure/document_processing/extraction/
        v
Skill normalization (alias -> canonical Skill)         -- domain/skills/normalization.py
        v
Persistence (Django models)                            -- infrastructure/database/repositories/
```

Orchestrated end-to-end by `application/cv/process_pipeline.py` and
`application/jobs/process_pipeline.py`, run asynchronously by
`workers/tasks/document_tasks.py`.

## Composition root

`config/container.py` is the only module allowed to import both
`application/*` use cases and concrete `infrastructure/*` classes. It
wires the Django-backed repositories, the rule-based extractors, and the
storage/parser implementations together. `interfaces/api/*` views and
`workers/tasks/*` both call `config/container.py` factory functions
instead of constructing use cases themselves - see
[dependency-rule.md](dependency-rule.md) for why this matters: it keeps
`application/` importing nothing but `domain/` and the standard library,
even though something, somewhere, has to know that `RuleBasedCandidateExtractor`
is the current `CandidateExtractor` implementation.

## Duplicate upload handling

**Decision: reuse the existing document.** Uploading a file whose SHA-256
hash already exists (for the same `document_type` and owner) returns the
existing `Document` instead of creating a new row or rejecting the
upload. See `application/documents/upload_document.py::UploadDocument`.

Rationale: a duplicate upload is far more often a UI retry, a page
refresh, or the same file added from a different flow than a genuine
"new version" - and this repository does not yet have a concept of CV
*versions* (that would be a deliberate, separate feature). Reusing avoids
duplicate processing work and duplicate rows without silently discarding
the user's action: they still land on the same processed document.

## Idempotency

`ProcessCvDocumentPipeline.run()` / `ProcessJobDocumentPipeline.run()`
short-circuit immediately if the document is already `PROCESSED`. A
retried or duplicate Celery task execution is therefore a no-op. On a
genuine retry from `FAILED` or mid-`PROCESSING`, the pipeline re-parses
the same stored file and re-extracts; `candidate_profile_repository.py`
and `job_profile_repository.py` *replace* the previous structured rows
rather than appending to them, so re-running never creates duplicates.

`processing_metadata.extraction_version` is stored on every successful
run so a future phase that changes extraction logic has a documented way
to detect and re-process older documents - not implemented as an active
trigger in Phase 2 (see Known limitations).

## Confidence and evidence

Every extracted fact (a skill mention, an experience entry, a job
requirement, ...) carries an `Evidence` record: the exact source text,
its page number (PDF only - DOCX and plain text have no page concept),
its section, the extraction method, and a confidence value.

**`confidence` is extraction confidence, not truth.** A confidence of
0.95 on a skill means "the parser is confident it read and classified
this text correctly" - not "the candidate is 95% likely to know this
skill." See `domain/documents/evidence.py` for the full rationale. Later
phases (matching, scoring) must not reinterpret this number.

## Security baseline (Phase 2)

- File validation: extension, declared MIME type, and size are checked
  before anything is parsed (`domain/documents/policies.py`).
- Storage: `infrastructure/storage/local.py` writes under a fixed
  `MEDIA_ROOT/documents/` directory keyed by content hash. No
  interfaces/api endpoint exposes a raw file URL or a "download the
  original" action - the API only ever returns metadata and structured
  data.
- Access: there is still no authentication (a carryover from Phase 1).
  `Document.owner` is nullable and nothing scopes a document to a
  request's user. Any document's UUID is sufficient to read its status
  or profile. This is a deliberate, temporary development-only
  assumption, not a production access model - proper authorization is
  Phase 1/2's shared known limitation, to be addressed before any real
  deployment.
- Logging: `application/cv/process_pipeline.py` and
  `application/jobs/process_pipeline.py` log `document_id`, stage, and
  duration - never the document's extracted text or contents.

## Known limitations (rule-based extraction v1)

The extractors in `infrastructure/document_processing/extraction/` are a
deterministic first version, not a general CV/job parser:

- Experience/education entries are split on blank lines within a
  section; a CV that doesn't separate entries with a blank line will be
  read as a single entry.
- Title/company parsing tries a handful of common separators (`at`, `|`,
  `-`, `,`); an unusual format falls back to treating the whole line as
  the title with no company.
- Skills are only read from a detected SKILLS section - a skill
  mentioned only in prose (e.g. inside an experience bullet) is not
  separately extracted unless it also appears in the Skills section.
- Section detection is heading-based and English-oriented; a CV with no
  recognizable headings (or in another language) will mostly fall under
  a single `OTHER` section.
- Evidence is attached to `Experience`, `Education`, `Certification`,
  `CandidateSkillMention`, and `JobRequirement`. `Project` and `Language`
  do not carry dedicated evidence in Phase 2 - a scope reduction made to
  keep the persistence model proportional (see `apps/candidates/models.py`).

These are intentional v1 boundaries, not bugs - the architecture (the
`CandidateExtractor`/`JobExtractor` abstraction in
`infrastructure/document_processing/extraction/base.py`) is designed so a
smarter extractor (rule refinements, or an LLM-assisted one behind the
same interface) can replace `RuleBasedCandidateExtractor` /
`RuleBasedJobExtractor` later without touching `application/` or
`interfaces/`.
