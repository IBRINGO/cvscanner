# Phase 4 - Evidence-Aware Hybrid ATS Matching Engine

This document describes what Phase 4 built on top of Phase 2's
document intelligence pipeline and Phase 3's semantic enrichment (see
[phase-2-pipeline.md](phase-2-pipeline.md) and
[phase-3-semantics.md](phase-3-semantics.md)). Phase 2 answers "what
information is present in this document?"; Phase 3 answers "what does
that information mean, and how is it related?"; Phase 4 answers "how
well does this candidate meet this job's requirements, and why?"
Nothing in Phase 4 recommends changes, rewrites a CV, or ranks
candidates against each other - see "Phase 5 boundary" at the end.

## Why hybrid, not "embed and compare"

The obvious shortcut - embed the CV, embed the job, cosine-similarity
the two vectors, call that the score - is explicitly rejected. A single
similarity number cannot distinguish "the candidate has the exact
required skill" from "the candidate's CV happens to read similarly."
See [ADR 0003](../adr/0003-hybrid-matching-not-pure-embeddings.md) for
the full reasoning. Instead, each requirement is resolved through an
evidence hierarchy, strongest signal first:

```text
1. Exact match       - the requirement's own skill/text appears directly
2. Alias match        - a known alternate name/surface form appears
3. Ontology match      - a related skill appears (parent/child, ecosystem,
                         explicit relation) via Phase 3's relationship view
4. Semantic match     - embedding similarity, ONLY when 1-3 found nothing
5. No evidence         - none of the above
```

`domain/matching/enums.py::MatchSignal` names these five outcomes
(plus `PARTIAL_MATCH` for a requirement that is only partially
satisfiable, e.g. an unresolved free-text skill). A `RELATED_MATCH`
(layer 3) is never reported as equivalent to an `EXACT_MATCH` (layer
1) - Kubernetes required with only Docker on the CV always scores as
`RELATED_MATCH`/`PARTIAL` strength, never `EXACT_MATCH`. Every matcher
in `domain/matching/*_matching.py` follows this same layering for its
own requirement type (skills, experience, seniority, education,
certifications, languages, responsibilities, domain alignment).

## Where embeddings fit

Embeddings are computed by the **application** layer
(`application/matching/run_analysis.py`), never inside a domain
matcher. `RunAnalysis` calls the embedding provider only for:

* a required/preferred skill that resolved to `NO_EVIDENCE` through
  layers 1-3, and only when the requirement has a resolved
  `Skill` (not a bare free-text string), and
* a responsibility/role-alignment line whose lexical word-overlap with
  every candidate experience is below a small threshold.

`domain/matching/semantic.py::cosine_similarity` is pure Python (no
numpy) so the domain layer stays framework-free. A semantic match
never carries a `MatchEvidence` citation (there is no literal source
text asserting the match, only a computed similarity), and its
resulting `MatchStrength` is capped below `STRONG` by
`domain/matching/weights.py::SemanticMatchingConfig` - a good semantic
score can reach `GOOD` but never substitutes for a confirmed exact/
alias/ontology match.

## The eight matching dimensions

Each dimension has its own evaluation module and never inflates
another's evidence:

| Dimension | Module | Notable rule |
|---|---|---|
| Skills | `skill_matching.py` | Layered exact/alias/ontology/semantic per requirement |
| Experience | `experience_matching.py` | Merges overlapping date ranges before summing years; distinguishes "confidently zero" from "unparseable" (see Known limitations) |
| Seniority | `seniority_matching.py` | Compares the candidate's peak demonstrated seniority against the job's stated level; `UNKNOWN` is never treated as "does not meet" |
| Education | `education_matching.py` | Ranks degree levels on a ladder; `PROFESSIONAL_CERTIFICATE` is deliberately excluded from the ladder (not comparable to a degree) |
| Certifications | `certification_matching.py` | Consults only `CandidateProfile.certifications` - a matching skill is never treated as evidence of a certification |
| Languages | `language_matching.py` | Ordinal CEFR-style proficiency comparison; written and tested even though the current job extractor does not yet emit `LANGUAGE` requirements |
| Responsibilities | `responsibility_matching.py` | Lightweight lexical-overlap-then-semantic check against experience descriptions; supporting evidence only, capped weight |
| Domain alignment | `domain_alignment.py` | Compares the candidate's skill-domain distribution against the job's required domains; supporting evidence only |

`domain/matching/priority.py` maps Phase 2's `RequirementImportance`
(`REQUIRED`/`PREFERRED`) onto `RequirementPriority`
(`MANDATORY`/`PREFERRED`/`OPTIONAL` - `OPTIONAL` is reserved for
requirement types, like responsibilities, that never carry a
`REQUIRED`/`PREFERRED` importance in the first place).

## Deterministic, versioned scoring

`domain/matching/engine.py::compute_score_breakdown` never asks an LLM
for a number. It takes one already-computed score per dimension and
combines them with fixed weights from
`domain/matching/weights.py::MatchingWeights` (skills 0.30, experience
0.20, seniority 0.10, education 0.10, certifications 0.10, languages
0.05, responsibilities 0.10, domain 0.05 - every weight is justified in
that module's docstring and the dataclass validates the total is
exactly 1.0).

**Missing-dimension redistribution:** a dimension with zero
evaluations (e.g. a job posting with no certification requirements) is
excluded from the weighted average entirely - not scored as 0 (which
would unfairly punish the candidate for a dimension nobody asked
about) and not scored as 1 (which would fabricate credit). The
remaining dimensions' weights are used as-is against their own total
(a proportional renormalization), so the overall score always reflects
only what was actually asked for.

**Mandatory-requirement penalty:** a missing `MANDATORY` requirement
never zeroes out the score. Each missing mandatory requirement applies
a capped, additive penalty
(`MatchingWeights.mandatory_penalty_per_gap`, capped at
`mandatory_penalty_cap`) on top of the weighted dimension average, so
the full breakdown - which dimensions were strong, which mandatory
items are missing - is always visible instead of a single collapsed
zero.

`domain/matching/weights.py::MATCHING_ENGINE_VERSION` is stored on
every `Analysis` row (`engine_version`). A later change to the
weights, thresholds, or matcher logic bumps this version; existing
analyses keep the score they were computed with and are never silently
rescored.

## Gap detection

`domain/matching/engine.py::detect_gaps` turns every non-`MET`
requirement evaluation into a structured `Gap` (requirement type,
priority, reason, evidence status, related candidate skills,
confidence). This is deliberately **not** a recommendation - no gap
says what the candidate should do about it. That synthesis is Phase
5's job (see "Phase 5 boundary").

## Embedding providers

`infrastructure/embeddings/providers/`:

* `GeminiEmbeddingProvider` (`gemini-embedding-2`) - primary, used when
  `GEMINI_API_KEY` is configured.
* `OpenAIEmbeddingProvider` (`text-embedding-3-small`, from Phase 3) -
  fallback, used when `OPENAI_API_KEY` is configured.
* `FakeEmbeddingProvider` (from Phase 3) - deterministic, SHA-256-based
  vectors; used in tests and whenever no real provider is configured.

`FallbackEmbeddingProvider` tries each configured real provider in
order and tracks which one actually produced the last successful
result, so `SemanticRepresentation.embedding_model` never misattributes
an OpenAI-produced vector to Gemini or vice versa.
`config/container.py::build_embedding_provider` wires this chain from
whichever API keys are present; if none are configured, or every
configured provider fails at call time, `RunAnalysis` catches
`EmbeddingProviderError` and continues with lexical/ontology-only
matching for that requirement - a missing or failing embedding
provider degrades matching quality, never crashes an analysis.

## Persistence

`apps/analyses/models.py`: `Analysis` (status, engine_version,
overall_score, score_breakdown JSON, gaps JSON, metadata JSON,
error_message, timestamps) and `RequirementEvaluationRecord` (one row
per evaluated requirement, with its evidence list embedded as JSON).
Evidence and gaps are stored as JSON rather than separate tables
because they are read-only presentation snapshots of a specific
analysis run with no independent foreign-key targets of their own - see
the module docstring in `apps/analyses/models.py` for the full
reasoning (the same style of justification as
[ADR 0002](../adr/0002-json-embeddings-not-pgvector.md) for embeddings).

No uniqueness constraint exists on `(candidate_document, job_document)`
- this is deliberate. Re-running an analysis after the engine version
changes (or simply to see a fresh run) creates a new row; history is
preserved rather than overwritten.

## Orchestration

`application/matching/create_analysis.py::CreateAnalysis` validates
both documents are `CV`/`JOB_OFFER` and `PROCESSED`, then creates the
`Analysis` row in `PENDING` synchronously (so the API can return an id
immediately). `application/matching/run_analysis.py::RunAnalysis` does
the actual matching and is invoked by the Celery task
`workers.analyses.run_analysis`. The task is idempotent: it operates on
the pre-existing `analysis_id`, and `save_result` replaces (not
appends) that analysis's requirement evaluations, so a Celery retry
never duplicates rows.

## API surface

* `POST /api/v1/analyses/` - body `{"candidate_document_id", "job_document_id"}`; `202` + queues matching. `400` if either document is not a processed CV/job offer.
* `GET /api/v1/analyses/` - list, newest first.
* `GET /api/v1/analyses/{id}/` - full detail: `score_breakdown`, `requirement_evaluations` (each with `match_signal`, `match_strength`, `explanation`, `evidence`), `gaps`.
* `GET /api/v1/analyses/{id}/status/` - lightweight polling endpoint (status, error, completed_at) for the frontend's processing view.

Uploading is never repeated here - both endpoints take the `id`s of
CV/job documents already uploaded and processed through the Phase 2
pipeline.

## Frontend

`frontend/src/app/features/analysis/`: `analysis-list` (a candidate/job
picker plus analysis history) and `analysis-detail` (the workspace
itself - candidate/job context header, a typographic overall score with
a plain-language interpretation, a horizontal-bar score breakdown by
dimension, an expandable requirement matrix where each row reveals its
evidence explorer, and a structured gap section). State is plain
Angular Signals; `pollUntilDone` (from Phase 2) is reused to poll
`.../status/` while an analysis is `PENDING`/`PROCESSING`. The loading
state shows named processing stages ("Reading requirements", "Checking
skills", ...) rather than a fabricated progress percentage.

## Known limitations (Phase 4 v1)

* **Experience date parsing** only handles the date phrasings Phase 2's
  extractor already produces; when a technology-filtered set of
  experiences exists but their dates cannot be parsed, the requirement
  evaluation reports `UNKNOWN` (a genuine "we can't tell" signal) rather
  than a fabricated year count - this is different from "no matching
  experience at all," which confidently reports zero years.
* **Responsibility/domain alignment are intentionally lightweight** -
  Jaccard word-overlap plus an optional semantic fallback, capped to a
  small share of the overall score (0.10 and 0.05 respectively). They
  are supporting evidence, not a primary signal.
* **Language requirements are matched but never produced** - the
  current job extractor (Phase 2) does not yet emit `LANGUAGE`-type
  requirements from job postings, so `language_matching.py` is
  exercised by unit tests but rarely by real end-to-end data yet.
* **No cross-candidate ranking** - an analysis is always one CV against
  one job offer. Comparing multiple candidates for the same job is out
  of scope for Phase 4 (and is not currently planned as a later phase
  either, since CVScanner's stated purpose is per-candidate feedback,
  not recruiter tooling).
* **Embeddings remain JSON, not indexed** - unchanged from
  [ADR 0002](../adr/0002-json-embeddings-not-pgvector.md); Phase 4 does
  not perform nearest-neighbor search, only pairwise cosine similarity
  between exactly two already-known vectors.

## Phase 5 boundary

Phase 4 stops at **explaining** the analysis: a score, a breakdown, and
a list of structured gaps. It never suggests what the candidate should
do, never rewrites CV content, never generates a cover letter, and
never compares candidates against each other. Turning a `Gap` into an
actionable recommendation - and everything CV-tailoring or
claim-validation related - is Phase 5 and Phase 6's job.
