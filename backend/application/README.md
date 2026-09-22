# application/

Use cases that orchestrate `domain/` objects and infrastructure
abstractions (received as duck-typed constructor parameters - see
[dependency-rule.md](../../docs/architecture/dependency-rule.md)). Views
in `interfaces/api/` call into these through `config/container.py` - they
should never contain business logic themselves.

| Module              | Holds                                                             | Status (Phase) |
|---------------------|---------------------------------------------------------------------|----------------|
| `documents/`        | `UploadDocument`, `ParseDocument` (shared by CVs and job offers)      | Implemented (2)|
| `cv/`               | `ExtractCandidateProfile`, `ProcessCvDocumentPipeline`               | Implemented (2)|
| `jobs/`             | `ExtractJobProfile`, `ProcessJobDocumentPipeline`                    | Implemented (2)|
| `matching/`         | `MatchRequirements`, `RetrieveEvidence`, `RankMatches`               | Phase 3        |
| `scoring/`          | `CalculateAtsScore`                                                  | Phase 4        |
| `recommendations/`  | `GenerateRecommendations`                                            | Phase 4        |
| `tailoring/`        | `GenerateTailoredCV`, `ValidateTailoredCV`                           | Phase 5        |

Skill normalization has no dedicated use case module - it happens inside
the extraction use cases (`ExtractCandidateProfile`/`ExtractJobProfile`
via the injected extractor), since it is one inseparable step of turning
raw text into a structured profile, not a standalone operation with its
own trigger.
