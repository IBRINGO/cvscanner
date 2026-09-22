# application/

Use cases that orchestrate `domain/` objects and infrastructure
abstractions (received as duck-typed constructor parameters - see
[dependency-rule.md](../../docs/architecture/dependency-rule.md)). Views
in `interfaces/api/` call into these through `config/container.py` - they
should never contain business logic themselves.

| Module              | Holds                                                             | Status (Phase) |
|---------------------|---------------------------------------------------------------------|----------------|
| `documents/`        | `UploadDocument`, `ParseDocument` (shared by CVs and job offers)      | Implemented (2)|
| `cv/`               | `ExtractCandidateProfile`, `ProcessCvDocumentPipeline` (now also runs enrichment/embedding - see below) | Implemented (2, extended 3) |
| `jobs/`             | `ExtractJobProfile`, `ProcessJobDocumentPipeline` (same extension)   | Implemented (2, extended 3) |
| `semantics/`        | `EnrichCandidateProfile`, `EnrichJobProfile`, `GenerateSemanticEmbeddings` | Implemented (3)|
| `matching/`         | `MatchRequirements`, `RetrieveEvidence`, `RankMatches`               | Phase 4        |
| `scoring/`          | `CalculateAtsScore`                                                  | Phase 5        |
| `recommendations/`  | `GenerateRecommendations`                                            | Phase 5        |
| `tailoring/`        | `GenerateTailoredCV`, `ValidateTailoredCV`                           | Phase 6        |

Phase 3's enrichment use cases run as a second, isolated step inside the
same pipeline - see
[docs/architecture/phase-3-semantics.md](../../docs/architecture/phase-3-semantics.md)
for the failure-isolation rationale (an enrichment/embedding failure
never marks a document `FAILED`).

Skill normalization has no dedicated use case module - it happens inside
the extraction use cases (`ExtractCandidateProfile`/`ExtractJobProfile`
via the injected extractor), since it is one inseparable step of turning
raw text into a structured profile, not a standalone operation with its
own trigger.
