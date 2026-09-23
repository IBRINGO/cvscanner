"""Builds a `TailoringPlan` from selected recommendations (Phase 5
section 27) - deterministic, no LLM call. This is the step that decides
*what* will be touched; `application/tailoring/run_tailoring.py`
decides *how* (deterministic rewrite for CONSERVATIVE, LLM-assisted for
AGGRESSIVE_SAFE) and validates the result through the Truth Layer.

Only recommendations `Recommendation.safe_to_tailor` are ever turned
into an operation (section 11) - a NOT_SAFE_TO_AUTOMATE or
REQUIRES_CANDIDATE_CONFIRMATION recommendation never appears in a plan;
the candidate acts on those manually.
"""
import re

from domain.cv.entities import CandidateProfile, Experience
from domain.recommendations.entities import Recommendation
from domain.recommendations.enums import RecommendationType
from domain.tailoring.entities import SectionOperation, TailoringPlan
from domain.tailoring.enums import TailoringMode
from domain.truth.entities import CandidateFact
from domain.truth.enums import AllowedTransformation, FactType

_LABEL_PATTERN = re.compile(r"(?:with|to) (.+)\.$")


def _experience_label(experience: Experience) -> str:
    parts = [part for part in (experience.title, experience.company) if part]
    return " at ".join(parts) if parts else "an experience entry"


def _find_target_fact(
    recommendation: Recommendation, facts: tuple[CandidateFact, ...], profile: CandidateProfile
) -> CandidateFact | None:
    if recommendation.type == RecommendationType.KEYWORD_PLACEMENT:
        for fact in facts:
            if fact.type == FactType.SKILL and fact.value == recommendation.current_state:
                return fact
        return None

    if recommendation.type == RecommendationType.RESPONSIBILITY_ALIGNMENT:
        match = _LABEL_PATTERN.search(recommendation.reason)
        if match is None:
            return None
        label = match.group(1)
        for index, experience in enumerate(profile.experiences):
            if _experience_label(experience) == label:
                fact_id = f"experience:{index}"
                return next((fact for fact in facts if fact.id == fact_id), None)
        return None

    return None


def build_tailoring_plan(
    *,
    analysis_id: str,
    source_cv_document_id: str,
    target_job_document_id: str,
    mode: TailoringMode,
    engine_version: str,
    facts: tuple[CandidateFact, ...],
    recommendations: tuple[Recommendation, ...],
    profile: CandidateProfile,
) -> TailoringPlan:
    operations: list[SectionOperation] = []
    targeted_fact_ids: set[str] = set()

    for recommendation in recommendations:
        if not recommendation.safe_to_tailor:
            continue
        fact = _find_target_fact(recommendation, facts, profile)
        if fact is None:
            continue
        transformation = AllowedTransformation.REPHRASE
        if not fact.permits(transformation):
            continue
        if fact.id in targeted_fact_ids:
            continue
        operations.append(
            SectionOperation(
                fact_id=fact.id,
                transformation=transformation,
                recommendation_title=recommendation.title,
                target_state=recommendation.target_state,
            )
        )
        targeted_fact_ids.add(fact.id)

    protected_fact_ids = tuple(fact.id for fact in facts if fact.id not in targeted_fact_ids)

    return TailoringPlan(
        analysis_id=analysis_id,
        source_cv_document_id=source_cv_document_id,
        target_job_document_id=target_job_document_id,
        mode=mode,
        engine_version=engine_version,
        operations=tuple(operations),
        protected_fact_ids=protected_fact_ids,
    )
