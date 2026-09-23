"""Runs the full hybrid matching pipeline for one analysis (Phase 4
sections 2, 5-24). This is the one place that dispatches each
JobRequirement to its dimension-specific matcher, decides when a
semantic (embedding) lookup is worth attempting, and assembles the
final ATSAnalysis via the domain scoring/gap-detection functions.

Domain/matching/*.py functions never call an embedding provider
directly (dependency rule) - this use case is exactly the layer that
decides *when* to spend an embedding call (only for requirements/
responsibilities the cheaper lexical/ontology layers left unresolved -
section 8 Layer 4, section 67 performance guidance) and feeds the
resulting similarity score back into the same domain matcher functions.

Embedding failures never fail the analysis (sections 29/62/80): every
call to the provider is wrapped, and a failure simply means that one
signal stays unavailable - lexical/ontology/evidence matching already
produced a valid result before semantic matching was ever attempted.

    candidate_profile_repository needs: get(document_id) -> CandidateProfile | None
    job_profile_repository needs: get(document_id) -> JobProfile | None
    skill_repository needs: all() -> list[Skill]
    analysis_repository needs: get_document_pair, mark_processing, save_result, mark_failed
    embedding_provider needs: embed(texts: list[str]) -> list[list[float]]
"""
import logging

from domain.cv.entities import CandidateProfile, Experience
from domain.job.entities import JobProfile, JobRequirement
from domain.job.enums import RequirementType
from domain.matching.candidate_index import build_candidate_skill_index
from domain.matching.certification_matching import evaluate_certification_requirement
from domain.matching.domain_alignment import evaluate_domain_alignment
from domain.matching.education_matching import evaluate_education_requirement
from domain.matching.engine import compute_score_breakdown, detect_gaps
from domain.matching.entities import ATSAnalysis, RequirementEvaluation
from domain.matching.enums import AnalysisStatus, MatchSignal
from domain.matching.experience_matching import evaluate_experience_requirement
from domain.matching.language_matching import evaluate_language_requirement
from domain.matching.responsibility_matching import best_lexical_match, evaluate_responsibility
from domain.matching.semantic import cosine_similarity
from domain.matching.seniority_matching import evaluate_seniority_requirement
from domain.matching.skill_matching import evaluate_skill_requirement
from domain.matching.weights import (
    DEFAULT_SEMANTIC_CONFIG,
    DEFAULT_WEIGHTS,
    MatchingWeights,
    SemanticMatchingConfig,
)
from infrastructure.embeddings.base import EmbeddingProviderError

logger = logging.getLogger(__name__)

_LEXICAL_OVERLAP_THRESHOLD = 0.25
_SKILL_REQUIREMENT_TYPES = (RequirementType.REQUIRED_SKILL, RequirementType.PREFERRED_SKILL)


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
        self._skill_repository = skill_repository
        self._analysis_repository = analysis_repository
        self._embedding_provider = embedding_provider
        self._engine_version = engine_version
        self._weights = weights
        self._semantic_config = semantic_config

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

            all_skills = self._skill_repository.all()
            candidate_index = build_candidate_skill_index(candidate)

            skill_evaluations = self._evaluate_skills(job, candidate_index, all_skills)
            experience_evaluations = tuple(
                evaluate_experience_requirement(requirement, candidate.experiences)
                for requirement in job.requirements
                if requirement.requirement_type == RequirementType.EXPERIENCE
            )
            education_evaluations = tuple(
                evaluate_education_requirement(requirement, candidate)
                for requirement in job.requirements
                if requirement.requirement_type == RequirementType.EDUCATION
            )
            certification_evaluations = tuple(
                evaluate_certification_requirement(requirement, candidate)
                for requirement in job.requirements
                if requirement.requirement_type == RequirementType.CERTIFICATION
            )
            language_evaluations = tuple(
                evaluate_language_requirement(requirement, candidate)
                for requirement in job.requirements
                if requirement.requirement_type == RequirementType.LANGUAGE
            )

            seniority_result = evaluate_seniority_requirement(job, candidate)
            seniority_evaluations = (seniority_result,) if seniority_result is not None else ()

            domain_result = evaluate_domain_alignment(job, candidate)
            domain_evaluations = (domain_result,) if domain_result is not None else ()

            responsibility_evaluations = self._evaluate_responsibilities(job, candidate)

            all_evaluations = (
                skill_evaluations
                + experience_evaluations
                + seniority_evaluations
                + education_evaluations
                + certification_evaluations
                + language_evaluations
                + responsibility_evaluations
                + domain_evaluations
            )

            breakdown = compute_score_breakdown(
                skills=skill_evaluations,
                experience=experience_evaluations,
                seniority=seniority_evaluations,
                education=education_evaluations,
                certifications=certification_evaluations,
                languages=language_evaluations,
                responsibilities=responsibility_evaluations,
                domain=domain_evaluations,
                weights=self._weights,
            )
            gaps = detect_gaps(all_evaluations)

            analysis = ATSAnalysis(
                candidate_document_id=candidate_document_id,
                job_document_id=job_document_id,
                engine_version=self._engine_version,
                status=AnalysisStatus.COMPLETED,
                overall_score=breakdown.overall,
                score_breakdown=breakdown,
                requirement_evaluations=all_evaluations,
                gaps=gaps,
            )
            self._analysis_repository.save_result(analysis_id, analysis)
            logger.info(
                "analysis.completed analysis_id=%s overall_score=%.4f", analysis_id, breakdown.overall
            )
        except Exception:
            self._analysis_repository.mark_failed(
                analysis_id, "An unexpected error occurred while running the analysis."
            )
            logger.exception("analysis.failed analysis_id=%s", analysis_id)
            raise

    def _evaluate_skills(
        self, job: JobProfile, candidate_index, all_skills
    ) -> tuple[RequirementEvaluation, ...]:
        evaluations = []
        for requirement in job.requirements:
            if requirement.requirement_type not in _SKILL_REQUIREMENT_TYPES:
                continue
            evaluation = evaluate_skill_requirement(requirement, candidate_index, all_skills)
            if evaluation.match_signal == MatchSignal.NO_EVIDENCE and requirement.skill is not None:
                semantic_score = self._compute_skill_semantic_score(requirement, candidate_index)
                if semantic_score is not None:
                    evaluation = evaluate_skill_requirement(
                        requirement,
                        candidate_index,
                        all_skills,
                        semantic_score=semantic_score,
                        semantic_config=self._semantic_config,
                    )
            evaluations.append(evaluation)
        return tuple(evaluations)

    def _compute_skill_semantic_score(self, requirement: JobRequirement, candidate_index) -> float | None:
        candidate_text = " ".join(candidate_index.keys())
        if not candidate_text.strip() or requirement.skill is None:
            return None
        try:
            vectors = self._embedding_provider.embed([requirement.skill.canonical_name, candidate_text])
        except EmbeddingProviderError:
            logger.warning(
                "analysis.semantic_unavailable dimension=skills requirement=%s", requirement.raw_text
            )
            return None
        return cosine_similarity(vectors[0], vectors[1])

    def _evaluate_responsibilities(
        self, job: JobProfile, candidate: CandidateProfile
    ) -> tuple[RequirementEvaluation, ...]:
        evaluations = []
        for responsibility_text in job.responsibilities:
            lexical = best_lexical_match(responsibility_text, candidate.experiences)
            semantic_score, semantic_experience = None, None
            if lexical.overlap < _LEXICAL_OVERLAP_THRESHOLD:
                semantic_score, semantic_experience = self._compute_responsibility_semantic_score(
                    responsibility_text, candidate.experiences
                )
            evaluations.append(
                evaluate_responsibility(
                    responsibility_text,
                    candidate.experiences,
                    semantic_score=semantic_score,
                    semantic_match_experience=semantic_experience,
                    semantic_config=self._semantic_config,
                )
            )
        return tuple(evaluations)

    def _compute_responsibility_semantic_score(
        self, responsibility_text: str, experiences: tuple[Experience, ...]
    ) -> tuple[float | None, Experience | None]:
        candidates = [experience for experience in experiences if experience.description]
        if not candidates:
            return None, None
        try:
            vectors = self._embedding_provider.embed(
                [responsibility_text] + [experience.description for experience in candidates]
            )
        except EmbeddingProviderError:
            logger.warning("analysis.semantic_unavailable dimension=responsibilities")
            return None, None

        target = vectors[0]
        best_score, best_experience = 0.0, None
        for experience, vector in zip(candidates, vectors[1:], strict=True):
            score = cosine_similarity(target, vector)
            if score > best_score:
                best_score, best_experience = score, experience
        return (best_score, best_experience) if best_experience is not None else (None, None)
