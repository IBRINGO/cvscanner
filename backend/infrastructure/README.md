# infrastructure/

Technical implementations of the abstractions `domain/`/`application/`
define: persistence, document parsing, LLM/embedding providers, search,
storage, cache, and observability. This is the only layer allowed to
import Django's ORM and vendor SDKs directly. See
[dependency-rule.md](../../docs/architecture/dependency-rule.md).

Reserved modules (empty in Phase 1, populated starting Phase 2):

| Module                   | Will eventually hold                                  |
|---------------------------|--------------------------------------------------------|
| `database/repositories/`  | Postgres-backed repository implementations              |
| `document_processing/`    | PDF/DOCX parsers, text extraction, OCR                   |
| `llm/`                     | `LLMProvider` abstraction + OpenAI/Gemini/mock providers |
| `embeddings/`              | `EmbeddingProvider` abstraction + providers              |
| `vector_store/`            | pgvector-backed vector search                            |
| `search/`                  | Lexical, semantic, and hybrid search                     |
| `storage/`                 | S3-compatible object storage                             |
| `cache/`                   | Redis-backed caching helpers                             |
| `observability/`           | Structured logging/metrics/tracing helpers beyond the base Django `LOGGING` config in `config/settings/base.py` |
