# infrastructure/

Technical implementations of the abstractions `domain/`/`application/`
define: persistence, document parsing, LLM/embedding providers, search,
storage, cache, and observability. This is the only layer allowed to
import Django's ORM and vendor SDKs directly. See
[dependency-rule.md](../../docs/architecture/dependency-rule.md).

| Module                        | Holds                                                          | Status (Phase) |
|-------------------------------|-----------------------------------------------------------------|----------------|
| `database/repositories/`      | Django ORM-backed `DocumentRepository`, `CandidateProfileRepository`/`CandidateEnrichmentRepository`, `JobProfileRepository`/`JobEnrichmentRepository`, `SkillRepository`, `SemanticRepresentationRepository` | Implemented (2, extended 3) |
| `document_processing/parsers/`| `DocumentParser` abstraction + `PDFParser`, `DOCXParser`, `PlainTextParser`, registry | Implemented (2) |
| `document_processing/extraction/` | `CandidateExtractor`/`JobExtractor` abstraction + rule-based implementations, contact-info regex helpers | Implemented (2) |
| `storage/`                    | `FileStorage` abstraction + `LocalFileStorage` (dev)             | Implemented (2, local only) |
| `llm/`                        | `LLMProvider` abstraction + OpenAI/Gemini/mock providers          | Phase 6        |
| `embeddings/`                 | `EmbeddingProvider` abstraction + `FakeEmbeddingProvider`/`OpenAIEmbeddingProvider` | Implemented (3) |
| `vector_store/`               | pgvector-backed vector search                                    | Not yet needed - see [ADR 0002](../../docs/adr/0002-json-embeddings-not-pgvector.md) |
| `search/`                     | Lexical, semantic, and hybrid search                             | Phase 4        |
| `cache/`                      | Redis-backed caching helpers                                     | Not yet needed |
| `observability/`              | Structured logging/metrics/tracing helpers beyond the base Django `LOGGING` config in `config/settings/base.py` | Not yet needed |

`storage/` intentionally has no `S3Storage` yet - `FileStorage` is a
Protocol specifically so one can be added later (a real deployment would
need it) without any caller changing, but Phase 2 only needed to prove
local development works.
