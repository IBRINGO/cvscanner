"""Generates (or retrieves already-generated) recommendations for a
completed analysis (Phase 5 sections 6-13, 37).

Deterministic and cheap - unlike RunAnalysis (Phase 4) this never calls
an embedding provider, so it runs synchronously from the API view rather
than through Celery. Idempotent: a second call for the same
(analysis_id, engine_version) returns the already-persisted set rather
than recomputing and duplicating rows.
"""
from domain.recommendations.config import RECOMMENDATION_ENGINE_VERSION
from domain.recommendations.engine import generate_recommendations
from domain.recommendations.entities import Recommendation


class AnalysisNotCompletedError(Exception):
    pass


class GenerateRecommendations:
    def __init__(
        self,
        analysis_repository,
        recommendation_repository,
        engine_version: str = RECOMMENDATION_ENGINE_VERSION,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._recommendation_repository = recommendation_repository
        self._engine_version = engine_version

    def execute(self, analysis_id: str) -> tuple[Recommendation, ...]:
        existing = self._recommendation_repository.get_for_analysis(analysis_id, self._engine_version)
        if existing is not None:
            return existing

        evaluations = self._analysis_repository.get_requirement_evaluations(analysis_id)
        recommendations = generate_recommendations(evaluations)
        self._recommendation_repository.save(analysis_id, self._engine_version, recommendations)
        return recommendations
