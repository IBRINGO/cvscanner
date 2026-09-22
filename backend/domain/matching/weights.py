"""Centralized scoring configuration (section 20 of the Phase 4 brief:
"the exact weights should be centralized ... do not scatter magic
numbers"). Everything the deterministic scoring engine needs to turn
per-dimension scores into one overall score lives here, with its
rationale in this docstring - not scattered across matcher modules.

## Dimension weights

These are an internal, deterministic ATS heuristic - not a scientifically
validated model of hiring outcomes (section 20 explicitly forbids
claiming otherwise). The rationale for the relative sizes:

    skills          0.30  Heaviest - the most concrete, most verifiable
                           signal (an exact/alias/ontology match is
                           either present in the CV or it isn't).
    experience      0.20  Years-of-experience requirements are a common
                           hard filter in real job offers; second only
                           to skills in how often they gate a candidate.
    seniority       0.10  Correlated with both skills and experience,
                           so it is deliberately not weighted as heavily
                           as either.
    education       0.10  Frequently a formal gate, but rarely the
                           deciding factor once skills/experience match.
    certifications  0.10  Precise (a certification is held or it is
                           not) but usually optional/preferred rather
                           than mandatory in the source data.
    languages       0.05  Usually a binary gate (a required language is
                           either present or a hard blocker), not a
                           differentiator worth heavy weight.
    responsibilities 0.10 Meaningful role-fit signal, deliberately not
                           allowed to dominate (section 16: "do not let
                           responsibility similarity dominate").
    domain          0.05  Supporting evidence only (section 17) - the
                           lightest weight, alongside languages.

## Mandatory requirement handling

A missing MANDATORY requirement is never silently averaged away - see
domain/matching/scoring.py's `mandatory_gap_penalty` calculation, which
this module also configures (`mandatory_penalty_per_gap`,
`mandatory_penalty_cap`). The penalty is capped, not multiplicative
against zero, per section 21: "do not automatically force the entire
score to zero."

## Semantic thresholds

`SemanticMatchingConfig` thresholds are heuristic, calibrated by
inspection of the fixtures in tests/fixtures/, not a labeled evaluation
dataset (section 33/63 - "document that thresholds are heuristic and
should be calibrated later using evaluation datasets").
"""
from dataclasses import dataclass

MATCHING_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class MatchingWeights:
    skills: float = 0.30
    experience: float = 0.20
    seniority: float = 0.10
    education: float = 0.10
    certifications: float = 0.10
    languages: float = 0.05
    responsibilities: float = 0.10
    domain: float = 0.05

    # How much a single missing MANDATORY requirement subtracts from the
    # overall score, and the maximum total penalty regardless of how many
    # mandatory requirements are missing (section 21: explain the full
    # analysis, never just zero it out).
    mandatory_penalty_per_gap: float = 0.15
    mandatory_penalty_cap: float = 0.60

    def as_dict(self) -> dict[str, float]:
        return {
            "skills": self.skills,
            "experience": self.experience,
            "seniority": self.seniority,
            "education": self.education,
            "certifications": self.certifications,
            "languages": self.languages,
            "responsibilities": self.responsibilities,
            "domain": self.domain,
        }

    def __post_init__(self) -> None:
        total = sum(self.as_dict().values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"MatchingWeights dimension weights must sum to 1.0, got {total}")


@dataclass(frozen=True)
class SemanticMatchingConfig:
    strong_threshold: float = 0.82
    partial_threshold: float = 0.68


DEFAULT_WEIGHTS = MatchingWeights()
DEFAULT_SEMANTIC_CONFIG = SemanticMatchingConfig()
