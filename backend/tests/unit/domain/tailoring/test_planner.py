from domain.cv.entities import CandidateProfile, CandidateSkillMention, Contact, Experience
from domain.recommendations.entities import Recommendation
from domain.recommendations.enums import (
    RecommendationConfidence,
    RecommendationImpact,
    RecommendationPriority,
    RecommendationSafety,
    RecommendationType,
)
from domain.tailoring.enums import TailoringMode
from domain.tailoring.planner import build_tailoring_plan
from domain.truth.fact_extraction import build_candidate_facts


def _profile() -> CandidateProfile:
    return CandidateProfile(
        full_name="Jordan Rivera",
        contact=Contact(),
        summary=None,
        skills=(CandidateSkillMention(raw_text="Postgres", skill=None, evidence=None),),
        experiences=(
            Experience(
                title="Software Engineer",
                company="Northwind Labs",
                start_date_raw="2019",
                end_date_raw="2021",
                description="Built internal tooling.",
                evidence=None,
            ),
        ),
    )


def _keyword_recommendation() -> Recommendation:
    return Recommendation(
        type=RecommendationType.KEYWORD_PLACEMENT,
        priority=RecommendationPriority.LOW,
        confidence=RecommendationConfidence.HIGH,
        safety=RecommendationSafety.SAFE_TO_REPHRASE,
        impact=RecommendationImpact.LOW_IMPACT,
        title="Use the canonical name for PostgreSQL",
        summary="...",
        reason="...",
        suggested_action="...",
        current_state="Postgres",
        target_state="PostgreSQL",
    )


def _responsibility_recommendation() -> Recommendation:
    return Recommendation(
        type=RecommendationType.RESPONSIBILITY_ALIGNMENT,
        priority=RecommendationPriority.MEDIUM,
        confidence=RecommendationConfidence.MEDIUM,
        safety=RecommendationSafety.SAFE_TO_REPHRASE,
        impact=RecommendationImpact.MEDIUM_IMPACT,
        title="Make existing experience match: Design and maintain REST APIs",
        summary="...",
        reason="No direct wording overlap, but conceptually similar to Software Engineer at Northwind Labs.",
        suggested_action="...",
    )


def _not_safe_recommendation() -> Recommendation:
    return Recommendation(
        type=RecommendationType.MISSING_REQUIREMENT,
        priority=RecommendationPriority.CRITICAL,
        confidence=RecommendationConfidence.HIGH,
        safety=RecommendationSafety.NOT_SAFE_TO_AUTOMATE,
        impact=RecommendationImpact.HIGH_IMPACT,
        title="Missing skill: Kubernetes",
        summary="...",
        reason="...",
        suggested_action="...",
    )


class TestBuildTailoringPlan:
    def test_a_keyword_placement_recommendation_becomes_an_operation(self):
        profile = _profile()
        facts = build_candidate_facts(profile)
        plan = build_tailoring_plan(
            analysis_id="a1",
            source_cv_document_id="cv1",
            target_job_document_id="job1",
            mode=TailoringMode.CONSERVATIVE,
            engine_version="1.0.0",
            facts=facts,
            recommendations=(_keyword_recommendation(),),
            profile=profile,
        )
        assert len(plan.operations) == 1
        assert plan.operations[0].fact_id == "skill:0"

    def test_a_responsibility_recommendation_is_linked_to_the_right_experience(self):
        profile = _profile()
        facts = build_candidate_facts(profile)
        plan = build_tailoring_plan(
            analysis_id="a1",
            source_cv_document_id="cv1",
            target_job_document_id="job1",
            mode=TailoringMode.AGGRESSIVE_SAFE,
            engine_version="1.0.0",
            facts=facts,
            recommendations=(_responsibility_recommendation(),),
            profile=profile,
        )
        assert plan.operations[0].fact_id == "experience:0"

    def test_a_not_safe_recommendation_never_becomes_an_operation(self):
        profile = _profile()
        facts = build_candidate_facts(profile)
        plan = build_tailoring_plan(
            analysis_id="a1",
            source_cv_document_id="cv1",
            target_job_document_id="job1",
            mode=TailoringMode.CONSERVATIVE,
            engine_version="1.0.0",
            facts=facts,
            recommendations=(_not_safe_recommendation(),),
            profile=profile,
        )
        assert plan.operations == ()

    def test_untargeted_facts_are_listed_as_protected(self):
        profile = _profile()
        facts = build_candidate_facts(profile)
        plan = build_tailoring_plan(
            analysis_id="a1",
            source_cv_document_id="cv1",
            target_job_document_id="job1",
            mode=TailoringMode.CONSERVATIVE,
            engine_version="1.0.0",
            facts=facts,
            recommendations=(_keyword_recommendation(),),
            profile=profile,
        )
        assert "experience:0" in plan.protected_fact_ids
        assert "skill:0" not in plan.protected_fact_ids
