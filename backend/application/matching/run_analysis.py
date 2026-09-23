"""Runs the full hybrid matching pipeline for one analysis (Phase 4
sections 2, 5-24). The actual dimension-by-dimension matching and
scoring logic lives in application/matching/scoring.py::ProfileScorer -
extracted so Phase 5's tailoring re-analysis step can reuse the exact
same code path (docs/architecture/phase-5-recommendations-and-tailoring.md
"ATS re-analysis"). This use case is the persistence/orchestration shell
around it: load the profiles, call the scorer, save the result.

    candidate_profile_repository needs: get(document_id) -> CandidateProfile | None
    job_profile_repository needs: get(document_id) -> JobProfile | None
    skill_repository needs: all() -> list[Skill]
    analysis_repository needs: get_document_pair, mark_processing, save_result, mark_failed
    embedding_provider needs: embed(texts: list[str]) -> list[list[float]]
"""
import logging

from application.matching.scoring import ProfileScorer
from domain.matching.entities import ATSAnalysis
from domain.matching.enums import AnalysisStatus
from domain.matching.weights import (
    DEFAULT_SEMANTIC_CONFIG,
    DEFAULT_WEIGHTS,
    MatchingWeights,
    SemanticMatchingConfig,
)

logger = logging.getLogger(__name__)


class RunAnalysis:
    def __init__(
        self,
        candidate_profile_repository,
        job_profile_repository,
        skill_repository,
        analysis_repository,
        embedding_provider,
        engine_version: str,
        weights: MatchingWeights = DEFAULT_WEIGHTS,
        semantic_config: SemanticMatchingConfig = DEFAULT_SEMANTIC_CONFIG,
    ) -> None:
        self._candidate_profile_repository = candidate_profile_repository
        self._job_profile_repository = job_profile_repository
        self._analysis_repository = analysis_repository
        self._engine_version = engine_version
        self._scorer = ProfileScorer(skill_repository, embedding_provider, weights, semantic_config)

    def execute(self, analysis_id: str) -> None:
        logger.info("analysis.started analysis_id=%s", analysis_id)
        candidate_document_id, job_document_id = self._analysis_repository.get_document_pair(analysis_id)
        self._analysis_repository.mark_processing(analysis_id)

        try:
            candidate = self._candidate_profile_repository.get(candidate_document_id)
            job = self._job_profile_repository.get(job_document_id)
            if candidate is None or job is None:
                self._analysis_repository.mark_failed(
                    analysis_id, "The candidate or job profile could not be found."
                )
                logger.warning("analysis.failed analysis_id=%s reason=profile_not_found", analysis_id)
                return

            result = self._scorer.score(candidate, job)

            analysis = ATSAnalysis(
                candidate_document_id=candidate_document_id,
                job_document_id=job_document_id,
                engine_version=self._engine_version,
                status=AnalysisStatus.COMPLETED,
                overall_score=result.breakdown.overall,
                score_breakdown=result.breakdown,
                requirement_evaluations=result.evaluations,
                gaps=result.gaps,
            )
            self._analysis_repository.save_result(analysis_id, analysis)
            logger.info(
                "analysis.completed analysis_id=%s overall_score=%.4f",
                analysis_id,
                result.breakdown.overall,
            )
        except Exception:
            self._analysis_repository.mark_failed(
                analysis_id, "An unexpected error occurred while running the analysis."
            )
            logger.exception("analysis.failed analysis_id=%s", analysis_id)
            raise
