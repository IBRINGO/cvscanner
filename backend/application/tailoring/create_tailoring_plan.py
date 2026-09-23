"""Tailoring plan creation use case (Phase 5 sections 27-28, 38).

Deterministic and synchronous - building a plan never calls an LLM (see
domain/tailoring/planner.py) - so the API can return an inspectable plan
immediately (section 27/28: review recommendations, select some,
preview what will change, THEN generate). The actual rewriting/
validation happens asynchronously via RunTailoring once the candidate
confirms.

    analysis_repository needs: get_status, get_document_pair
    candidate_profile_repository needs: get(document_id) -> CandidateProfile | None
    recommendation_repository needs: get_selected(analysis_id, ids) -> tuple[Recommendation, ...]
    tailoring_repository needs: create_pending(TailoringPlan) -> str
"""
from domain.matching.enums import AnalysisStatus
from domain.tailoring.enums import TailoringMode
from domain.tailoring.planner import build_tailoring_plan
from domain.truth.fact_extraction import build_candidate_facts


class TailoringValidationError(Exception):
    pass


class CreateTailoringPlan:
    def __init__(
        self,
        analysis_repository,
        candidate_profile_repository,
        recommendation_repository,
        tailoring_repository,
        engine_version: str,
    ) -> None:
        self._analysis_repository = analysis_repository
        self._candidate_profile_repository = candidate_profile_repository
        self._recommendation_repository = recommendation_repository
        self._tailoring_repository = tailoring_repository
        self._engine_version = engine_version

    def execute(self, analysis_id: str, mode: TailoringMode, recommendation_ids: list[str]) -> str:
        if self._analysis_repository.get_status(analysis_id) != AnalysisStatus.COMPLETED:
            raise TailoringValidationError("The analysis must be completed before it can be tailored.")

        if not recommendation_ids:
            raise TailoringValidationError("At least one recommendation must be selected.")

        recommendations = self._recommendation_repository.get_selected(analysis_id, recommendation_ids)
        unsafe = [r for r in recommendations if not r.safe_to_tailor]
        if unsafe:
            raise TailoringValidationError(
                "One or more selected recommendations cannot be automated and must be addressed manually."
            )

        candidate_document_id, job_document_id = self._analysis_repository.get_document_pair(analysis_id)
        profile = self._candidate_profile_repository.get(candidate_document_id)
        if profile is None:
            raise TailoringValidationError("The candidate profile could not be found.")

        facts = build_candidate_facts(profile)
        plan = build_tailoring_plan(
            analysis_id=analysis_id,
            source_cv_document_id=candidate_document_id,
            target_job_document_id=job_document_id,
            mode=mode,
            engine_version=self._engine_version,
            facts=facts,
            recommendations=recommendations,
            profile=profile,
        )
        if not plan.operations:
            raise TailoringValidationError(
                "None of the selected recommendations could be mapped to a safe, automatable change."
            )

        return self._tailoring_repository.create_pending(plan)
