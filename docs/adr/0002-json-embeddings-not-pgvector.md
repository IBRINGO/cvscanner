# ADR 0002: Store embeddings as JSON, not pgvector

* Status: Accepted
* Date: 2026-09-22

## Context

Phase 3 introduces an `EmbeddingProvider` abstraction and a
`SemanticRepresentation` record (see
docs/architecture/phase-3-semantics.md) so that CandidateProfile and
JobProfile text can optionally be embedded for a future semantic search
or matching layer. PostgreSQL's `pgvector` extension is the obvious
long-term home for embeddings once real similarity search over a large
corpus is needed.

Nothing in Phase 3 actually performs similarity search yet - the brief
is explicit that Phase 3 is a foundation, not the matching engine
(section 28). No query in this phase does "find the nearest N
embeddings."

## Decision

Store each `SemanticRepresentation.embedding` as a plain
`JSONField` (a list of floats) on a normal Postgres table, not as a
`pgvector` column.

## Consequences

**Why this is fine now:**

* Adding `pgvector` means a new Postgres extension, a Docker image
  change, and a new migration dependency (`CREATE EXTENSION vector`) for
  a capability nothing queries yet - see section 27 of the brief:
  "Do not automatically introduce pgvector simply because embeddings now
  exist."
* JSON keeps `apps/semantics/models.py` fully provider-agnostic: any
  future embedding model/dimension count fits without a schema change.
* The `FakeEmbeddingProvider` used in development and tests produces
  small (32-dimension) vectors specifically so this stays cheap even
  without an index.

**What this defers, on purpose:**

* No indexed nearest-neighbor query is possible against this column
  today. A linear scan over JSON arrays would not scale past a small
  number of documents.
* When a later phase (the ATS Matching Engine, or a semantic search
  feature) needs real similarity search over a large corpus, revisit
  this decision: add the `pgvector` extension, an `ARRAY(FLOAT)` or
  `vector` column, and a migration that backfills existing
  `SemanticRepresentation` rows from the JSON column. Nothing in
  `domain/semantics/` or `application/semantics/` needs to change for
  that migration - both already depend only on the
  `EmbeddingProvider`/repository abstractions, not on how a vector is
  stored.
