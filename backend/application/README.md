# application/

Use cases that orchestrate `domain/` objects and infrastructure
abstractions. Views in `interfaces/api/` call into these — they should
never contain business logic themselves. See
[dependency-rule.md](../../docs/architecture/dependency-rule.md).

Reserved modules (empty in Phase 1, populated starting Phase 2):

| Module            | Will eventually hold                                     |
|--------------------|-----------------------------------------------------------|
| `cv/`              | `UploadCV`, `ParseCV`, `StructureCV`, `NormalizeCV`         |
| `jobs/`            | `CreateJob`, `ParseJob`, `StructureJob`                     |
| `analysis/`        | `CreateAnalysis`, `RunAnalysis`, `GetAnalysis`               |
| `matching/`        | `MatchRequirements`, `RetrieveEvidence`, `RankMatches`       |
| `scoring/`         | `CalculateAtsScore`                                          |
| `recommendations/` | `GenerateRecommendations`                                    |
| `tailoring/`       | `GenerateTailoredCV`, `ValidateTailoredCV`                   |
