# Phase 5 - Evidence-Backed Recommendations and CV Tailoring

This document describes what Phase 5 built on top of Phase 4's matching
engine (see [phase-4-matching.md](phase-4-matching.md)). Phase 4 answers
"how well does this candidate meet this job's requirements, and why?";
Phase 5 answers "what should the candidate do about it, and how can
CVScanner help them present it - without ever inventing anything?"

```text
ATS Analysis (Phase 4)
        |
Requirement Evaluations + Gaps
        |
Recommendation Engine (deterministic)
        |
Truth Layer (candidate facts + claim validation)
        |
Tailoring Plan (deterministic, inspectable before generation)
        |
Generation (deterministic rewrite, or LLM-assisted in AGGRESSIVE_SAFE)
        |
Truth Layer validation (independent of what the LLM claims)
        |
Phase 4 re-analysis (the SAME ProfileScorer, never a manual score)
```

## Why the Truth Layer is the architectural center of this phase

The fundamental risk in "AI-assisted CV improvement" is a system that
optimizes a score by inventing content. Every component in this phase
is built around preventing that, in this order of authority:

1. **CandidateProfile + Evidence** (Phase 2/3) - the only source of
   truth about what the candidate has actually done.
2. **CandidateFact** (`domain/truth/fact_extraction.py`) - a read-only
   re-projection of that profile into a shape the Truth Layer can
   reason about: what it is, how sure we are of it, and what may
   safely happen to its wording.
3. **The LLM** - never authoritative. It may only rephrase within the
   bounds a `CandidateFact` allows, and its output is independently
   re-checked, never trusted because it "said" something was true.
4. **Claim validation** (`domain/truth/claim_validation.py`) - the
   deterministic, code-based check that runs on every proposed
   sentence regardless of which mode or provider produced it.

This ordering means a generation step calling the LLM and a generation
step that never touches the LLM (CONSERVATIVE mode) go through the
exact same final gate before anything is accepted.

## Recommendation Engine

`domain/recommendations/engine.py::generate_recommendations` reads
Phase 4's own `RequirementEvaluation` objects for one analysis and
produces a `Recommendation` per relevant finding - never independent of
what Phase 4 actually found (no generic career advice). Each
`RequirementEvaluation`'s own matching-method confidence becomes the
`Recommendation.confidence` directly, rather than a second, disconnected
scale (`domain/documents/evidence.py`'s confidence semantics apply here
unchanged).

* **Priority** (`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`) is derived from the
  requirement's own priority (`MANDATORY`/`PREFERRED`/`OPTIONAL`) and
  whether the finding is a total absence or a partial/weak one - never
  from keyword frequency.
* **Safety** (`SAFE_TO_REPHRASE`/`SAFE_TO_REORDER`/
  `REQUIRES_CANDIDATE_CONFIRMATION`/`NOT_SAFE_TO_AUTOMATE`) decides
  whether a recommendation can ever become a `SectionOperation` in a
  `TailoringPlan`. A missing skill, missing certification, or missing
  education requirement is always `NOT_SAFE_TO_AUTOMATE` - there is no
  wording change that can honestly resolve a total absence.
* **Deduplication and a concise cap** (section 12/44 of the brief):
  identical `(type, title)` findings collapse to one, and low-priority
  findings beyond a configured cap are dropped after every
  CRITICAL/HIGH item is kept in full - see
  `domain/recommendations/config.py` for the exact threshold and why.

## Truth Layer

### Fact extraction

`build_candidate_facts` walks the candidate's skills, experiences,
projects, education, certifications, and languages once and produces
one `CandidateFact` per item. A fact with a direct `Evidence` record is
`VERIFIED`; one present in the structured profile without its own
evidence link is `SUPPORTED`. `INFERRED`/`UNKNOWN` are reserved for
facts a later reasoning step might add (e.g. a computed total years of
experience) - fact extraction itself never guesses.

Each fact's `allowed_transformations` is scoped to what actually makes
sense for that fact type: a `SKILL` fact permits `REORDER`/`REPHRASE`
only (a skill's *name* can be normalized, never invented); an
`EXPERIENCE` fact additionally permits `SUMMARIZE`/`CONDENSE`/
`EXPAND_WITH_EXISTING_EVIDENCE`; a `LANGUAGE` fact permits `REORDER`
only - proficiency wording is exactly the kind of claim section 72
tests guard against, so it is never in the allowed set to rephrase in
the first place.

### Claim validation

`domain/truth/claim_validation.py` is the independent safety net
(section 18: "do not rely solely on asking the LLM 'did you
hallucinate?'"). Every proposed section, from any mode, is checked
against five categories, composed in `validate_generated_text`:

| Check | Catches |
|---|---|
| `validate_technology_claims` | A skill/technology mentioned in the proposal that was not already in the original text and is not part of the candidate's genuinely known skill set (reuses Phase 3's `TechnologyMentionScanner`) |
| `validate_certification_claims` | Certification wording ("certified"/"certification"/"certificate") introduced where none existed |
| `validate_duration_claims` | A new or inflated years-of-experience figure exceeding an independently computed verified duration |
| `validate_education_claims` | A degree level higher than the candidate's verified highest education |
| `validate_language_claims` | A proficiency word ("native", "fluent", ...) ranking higher than the candidate's verified proficiency |

Each check is independently testable and every one of section 72's
five adversarial scenarios has its own test in
`tests/unit/domain/truth/test_claim_validation.py::TestAdversarialCases`.
A rejected proposal never disappears silently - the original text is
kept, and the rejection reason is stored and surfaced (section 57).

## Tailoring Engine

### Planning

`domain/tailoring/planner.py::build_tailoring_plan` is deterministic
and never calls an LLM. It only turns a `Recommendation` into a
`SectionOperation` when `Recommendation.safe_to_tailor` is true, and
only when it can identify the specific `CandidateFact` the
recommendation is about (a `KEYWORD_PLACEMENT` recommendation names its
own skill directly; a `RESPONSIBILITY_ALIGNMENT` recommendation is
matched back to the experience its own evaluation named). Every fact
not targeted by an operation is listed explicitly as `protected` -
inspectable before anything is generated (section 27/28).

### Generation

`application/tailoring/generation.py::generate_section_text` is where
`TailoringMode` changes behavior:

* **CONSERVATIVE** never calls an LLM. A `SKILL` fact's rephrase is a
  deterministic keyword normalization (e.g. "Postgres" -> "PostgreSQL",
  using the canonical name Phase 2/3's taxonomy already established -
  section 22). An `EXPERIENCE` fact's rephrase is left unchanged in
  this mode; CONSERVATIVE only ever touches what is already fully
  deterministic.
* **AGGRESSIVE_SAFE** calls the configured `LLMProvider`
  (`infrastructure/llm/` - Gemini primary, OpenAI fallback, a
  deterministic `FakeLLMProvider` for tests, mirroring the Phase 3/4
  embedding-provider chain exactly) for an `EXPERIENCE` fact's
  rephrase, with a prompt that explicitly forbids inventing facts and
  asks for a single-field JSON response (section 25/26). Whatever the
  model returns is never trusted on its own - it goes through the same
  claim validation as anything else, and any provider failure or
  unparseable response falls back to the original text unchanged
  (never a crash, never invented filler).

### Validation and re-analysis

Every proposed section is validated per the Truth Layer rules above
before being accepted. `application/tailoring/run_tailoring.py`'s
`RunTailoring` then rebuilds an in-memory `CandidateProfile` with only
the *accepted* changes applied (skill wording, experience description)
and re-scores it through `application/matching/scoring.py::ProfileScorer`
- the exact same class Phase 4's `RunAnalysis` uses for the original
analysis, not a second scoring implementation (section 73: "the score
must come from the existing Phase 4 engine"). Before/after scores and a
requirements-improved/unchanged/still-missing breakdown come from
comparing the two `ScoringResult`s directly.

**Deliberate simplification from a literal document round-trip:**
section 73 describes "Tailored CV -> Document/Profile extraction ->
Phase 4 matching engine." This implementation reuses the already-
structured `CandidateProfile` directly (substituting only the accepted
text into `description`/skill wording) rather than rendering a new CV
document and re-running Phase 2's extractor on it. Tailoring never
changes structure, only wording of facts the Truth Layer already
verified, so a render-then-re-extract round trip would only
reintroduce the same facts through a lossier path. The re-scoring still
runs through the unmodified Phase 4 engine either way.

## Persistence

`apps/recommendations/models.py::Recommendation` (one table - a
separate `RecommendationEvidence` table was rejected the same way Phase
4 rejected a separate evidence table for `RequirementEvaluationRecord`:
`supporting_evidence` is a read-only content snapshot, not an
independent fact). `apps/tailoring/models.py::TailoringPlan` and
`TailoringChange` (two tables, not four - `TailoringPlan` already
carries what the brief calls "TailoredCV" status/scores, and
`TailoringChange` already carries what the brief calls "TailoredSection"
original/final text and diff). See each model file's own docstring for
the full reasoning.

## API surface

* `GET /api/v1/analyses/{id}/recommendations/` - generates (once,
  idempotently) and returns recommendations for a completed analysis.
* `POST /api/v1/tailoring/` - body
  `{"analysis_id", "mode", "recommendation_ids"}`; `202` + queues
  `RunTailoring`. `400` if any selected recommendation is not
  `safe_to_tailor`, or the analysis is not `COMPLETED`.
* `GET /api/v1/tailoring/` - list.
* `GET /api/v1/tailoring/{id}/` - full detail: operations, protected
  facts, before/after scores, requirement deltas, changes.
* `GET /api/v1/tailoring/{id}/status/` - polling endpoint.
* `GET /api/v1/tailoring/{id}/changes/` - just the diff list.

## Frontend

`frontend/src/app/features/recommendations/` (`recommendations-page`,
scoped to one analysis - grouped by priority, a checkbox only where
`safe_to_tailor` is true, an expandable evidence explorer per row) and
`frontend/src/app/features/tailoring/` (`tailoring-detail` - an honest
progress timeline mapping directly to the real backend states
`PENDING`/`PLANNING`/`GENERATING`/`VALIDATING`, never a fabricated
percentage; before/after scores with an explicit non-guarantee
disclaimer; a factual-consistency summary; every change shown with an
inline word-level diff, accepted or rejected, never hidden). Both reuse
the semantic `--match-*` color tokens and icon set Phase 4 established
- no new visual language was introduced.

## Known limitations (Phase 5 v1)

* **Tailoring targets only `SKILL` and `EXPERIENCE` facts** - the two
  recommendation types the engine currently produces
  (`KEYWORD_PLACEMENT`, `RESPONSIBILITY_ALIGNMENT`) that are ever
  `SAFE_TO_REPHRASE`. Reordering (`SAFE_TO_REORDER`) is modeled in the
  domain but no current recommendation type produces it yet.
- **Multiple recommendations can collapse onto one fact** - if several
  responsibilities all best-match the same experience bullet, the
  planner deduplicates by fact id (only one edit can be planned per
  bullet without conflict), so the resulting change count can be lower
  than the number of recommendations selected. This is intentional, not
  a bug - see `domain/tailoring/planner.py`.
* **Structured LLM output is JSON-in-a-text-prompt, not a provider's
  native function-calling API** - kept intentionally simple so the same
  parsing works identically across Gemini and OpenAI (section 25's
  "prefer structured output" is satisfied by the contract, not by a
  provider-specific schema feature). A malformed response degrades to
  "keep the original text," never a crash.
* **No cross-candidate ranking, interview generation, or salary
  prediction** - explicitly out of scope (section 85).
* **Re-analysis reuses the structured profile, not a rendered-and-
  re-extracted document** - see "Validation and re-analysis" above.

## Non-goals (unchanged from the brief)

Autonomous job applications, recruiter workflows, candidate ranking,
interview generation, cover letter generation, salary/outcome
prediction, automatic external job submissions, fabricated candidate
experience, automatic acquisition of missing skills, automatic
certification claims.
