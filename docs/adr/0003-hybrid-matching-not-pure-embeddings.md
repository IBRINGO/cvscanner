# ADR 0003: Hybrid lexical/alias/ontology/semantic matching, not pure embedding similarity

* Status: Accepted
* Date: 2026-09-23

## Context

Phase 3 built an `EmbeddingProvider` abstraction and stores an optional
`SemanticRepresentation` per `CandidateProfile`/`JobProfile` (see
[ADR 0002](0002-json-embeddings-not-pgvector.md) and
[phase-3-semantics.md](../architecture/phase-3-semantics.md)), but
performed no comparison between them. Phase 4 needs to actually decide,
per job requirement, whether a candidate meets it - and produce a
score and an explanation a person can trust.

The simplest possible design is: embed the whole CV, embed the whole
job description, compute one cosine similarity, and call that the
match score. This is tempting because it requires almost no matching
logic. It is also the design this ADR rejects.

## Decision

Match each job requirement independently, through a fixed evidence
hierarchy, strongest signal first:

1. **Exact match** - the requirement's own skill/text is present in the
   candidate's profile (skill list, experience technologies, project
   technologies).
2. **Alias match** - a known alternate surface form of the same skill
   is present (e.g. "JS" for "JavaScript"), using Phase 2's existing
   alias data.
3. **Ontology match** - a *related* skill is present, using Phase 3's
   `build_relationship_view` (parent/child, ecosystem, explicit
   `RELATED_TO`/`ALTERNATIVE_TO`/`BUILDS_ON` relations). This is
   reported as `RELATED_MATCH`, never as an exact match.
4. **Semantic match** - only reached when layers 1-3 found nothing
   (or, for responsibilities, when lexical word-overlap is low). An
   embedding similarity above a configured threshold produces a
   `SEMANTIC_MATCH`, capped at `MatchStrength.GOOD` - never `STRONG`.
5. **No evidence** - none of the above; a gap.

A single overall document-to-document cosine similarity is never
computed or stored as part of the score. Embeddings are consulted
per-requirement, per-dimension, only as a last resort, from the
application layer (`RunAnalysis`), never inside a domain matcher.

Scoring itself is a deterministic weighted average over eight
dimensions (`domain/matching/engine.py`), never an LLM call and never
a function of the embedding similarity directly - the embedding only
decides *whether* a given requirement counts as met, at a capped
strength; it never sets the requirement's score itself. Every unmet
`MANDATORY` requirement applies a capped, additive penalty rather than
zeroing the score, so the breakdown stays informative.

## Consequences

**Why this is worth the extra complexity:**

* **Kubernetes required, Docker on the CV is a real, common case** that
  a single embedding-similarity number cannot distinguish from "the
  candidate has Kubernetes on their CV." Two CVs can produce a nearly
  identical whole-document embedding for very different reasons (same
  industry vocabulary, same job-title phrasing) without sharing the
  specific skills a requirement actually asks for. The hierarchy makes
  the four-way distinction (exact / related / semantically similar /
  absent) visible in the API response and the UI, not collapsed into
  one number.
* **Evidence is preservable.** An exact or alias match carries the
  actual `Evidence` (source text, page, section) that Phase 2 already
  extracted. A semantic match cannot honestly claim a source quote -
  there is no literal sentence saying "the candidate meets this
  requirement" - so it is presented with an explanation instead of a
  quote, and the UI clearly labels it `Semantic match`.
* **Determinism and auditability.** The score for a given
  `(candidate_document, job_document, engine_version)` triple is
  reproducible - no LLM sampling, no reliance on an external
  provider's response for anything but a same-text-in-same-vector-out
  embedding. A future engine-version bump can be diffed against the
  previous one on the same fixtures.
* **Graceful degradation.** Because embeddings are one signal among
  several rather than the mechanism, a missing or failing embedding
  provider (`GEMINI_API_KEY`/`OPENAI_API_KEY` both absent, or both
  providers erroring) degrades matching to lexical/ontology signals
  only - `RunAnalysis` catches `EmbeddingProviderError` per call and
  continues - rather than making the entire analysis dependent on a
  third-party API being reachable.

**What this costs, on purpose:**

* More matching code than a single similarity call - eight dimension
  modules, an evidence-hierarchy per skill requirement, a shared
  `MatchStrength`/`MatchSignal` vocabulary
  (`domain/matching/enums.py`) that every matcher must respect.
* The ontology layer is only as good as Phase 3's skill relationship
  data (parent/child, ecosystem, explicit relations) - a skill with no
  relations recorded falls straight from alias-match to semantic-match
  with no ontology step to help it.
* Responsibility and domain-alignment matching, which lean more on
  lexical overlap and semantic similarity than on structured facts, are
  deliberately capped to a small share of the overall weight
  (`MatchingWeights.responsibilities = 0.10`,
  `MatchingWeights.domain = 0.05`) precisely because they are the least
  evidence-grounded dimensions - see
  [phase-4-matching.md](../architecture/phase-4-matching.md) "Known
  limitations".
