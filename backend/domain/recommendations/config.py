"""Centralized, justified constants for the recommendation engine - the
same "no scattered magic numbers" discipline as
domain/matching/weights.py.
"""
from dataclasses import dataclass

RECOMMENDATION_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class RecommendationEngineConfig:
    """Thresholds for turning a RequirementEvaluation's own
    matching-method confidence (Evidence.confidence semantics - see
    domain/documents/evidence.py) into a RecommendationConfidence.
    Reused as-is rather than inventing a second, parallel confidence
    scale.
    """

    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.60

    # section 12/44: a candidate should receive a concise, high-value
    # action plan, not dozens of independent items. This caps how many
    # MEDIUM/LOW priority recommendations survive after CRITICAL/HIGH
    # ones are always kept in full.
    max_medium_or_lower_recommendations: int = 8


DEFAULT_CONFIG = RecommendationEngineConfig()
