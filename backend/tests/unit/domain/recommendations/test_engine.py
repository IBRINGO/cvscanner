from domain.job.enums import RequirementType
from domain.matching.entities import RequirementEvaluation
from domain.matching.enums import MatchSignal, MatchStrength, RequirementPriority, RequirementStatus
from domain.recommendations.engine import generate_recommendations
from domain.recommendations.enums import (
    RecommendationPriority,
    RecommendationSafety,
    RecommendationType,
)


def _evaluation(
    requirement_type=RequirementType.REQUIRED_SKILL,
    priority=RequirementPriority.MANDATORY,
    status=RequirementStatus.NOT_MET,
    signal=MatchSignal.NO_EVIDENCE,
    confidence=0.9,
    raw_text="Kubernetes",
    matched_skill=None,
) -> RequirementEvaluation:
    return RequirementEvaluation(
        requirement_type=requirement_type,
        priority=priority,
        raw_text=raw_text,
        status=status,
        match_signal=signal,
        match_strength=MatchStrength.NONE,
        score=0.0,
        confidence=confidence,
        matched_skill=matched_skill,
        explanation=f"No evidence of {raw_text}.",
    )


class TestMissingRequirement:
    def test_missing_mandatory_skill_is_critical_and_not_automatable(self):
        recommendations = generate_recommendations((_evaluation(),))
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.type == RecommendationType.MISSING_REQUIREMENT
        assert rec.priority == RecommendationPriority.CRITICAL
        assert rec.safety == RecommendationSafety.NOT_SAFE_TO_AUTOMATE

    def test_missing_preferred_skill_is_high_not_critical(self):
        recommendations = generate_recommendations(
            (_evaluation(priority=RequirementPriority.PREFERRED),)
        )
        assert recommendations[0].priority == RecommendationPriority.HIGH

    def test_missing_certification_is_never_safe_to_automate(self):
        evaluation = _evaluation(
            requirement_type=RequirementType.CERTIFICATION,
            raw_text="AWS Certified Solutions Architect",
        )
        recommendations = generate_recommendations((evaluation,))
        assert recommendations[0].type == RecommendationType.CERTIFICATION_GAP
        assert recommendations[0].safety == RecommendationSafety.NOT_SAFE_TO_AUTOMATE


class TestRelatedAndSemanticMatches:
    def test_related_match_is_underrepresented_skill_requiring_confirmation(self):
        evaluation = _evaluation(
            status=RequirementStatus.PARTIALLY_MET,
            signal=MatchSignal.RELATED_MATCH,
            matched_skill="Docker",
        )
        recommendations = generate_recommendations((evaluation,))
        rec = recommendations[0]
        assert rec.type == RecommendationType.UNDERREPRESENTED_SKILL
        assert rec.safety == RecommendationSafety.REQUIRES_CANDIDATE_CONFIRMATION

    def test_alias_match_is_safe_keyword_placement(self):
        evaluation = _evaluation(
            status=RequirementStatus.MET,
            signal=MatchSignal.ALIAS_MATCH,
            raw_text="PostgreSQL",
            matched_skill="PostgreSQL",
            confidence=0.95,
        )
        recommendations = generate_recommendations((evaluation,))
        rec = recommendations[0]
        assert rec.type == RecommendationType.KEYWORD_PLACEMENT
        assert rec.safety == RecommendationSafety.SAFE_TO_REPHRASE


class TestNoRecommendationNoise:
    def test_fully_met_exact_match_produces_no_recommendation(self):
        evaluation = _evaluation(status=RequirementStatus.MET, signal=MatchSignal.EXACT_MATCH)
        assert generate_recommendations((evaluation,)) == ()

    def test_domain_alignment_type_is_never_commented_on(self):
        evaluation = _evaluation(
            requirement_type=RequirementType.OTHER,
            status=RequirementStatus.NOT_MET,
        )
        assert generate_recommendations((evaluation,)) == ()


class TestResponsibilityAlignment:
    def test_partial_responsibility_match_is_safe_to_rephrase(self):
        evaluation = _evaluation(
            requirement_type=RequirementType.RESPONSIBILITY,
            priority=RequirementPriority.OPTIONAL,
            status=RequirementStatus.PARTIALLY_MET,
            signal=MatchSignal.SEMANTIC_MATCH,
            confidence=0.65,
        )
        recommendations = generate_recommendations((evaluation,))
        rec = recommendations[0]
        assert rec.type == RecommendationType.RESPONSIBILITY_ALIGNMENT
        assert rec.safety == RecommendationSafety.SAFE_TO_REPHRASE


class TestExperienceClarification:
    def test_unknown_experience_status_asks_for_confirmation_not_automation(self):
        evaluation = _evaluation(
            requirement_type=RequirementType.EXPERIENCE,
            status=RequirementStatus.UNKNOWN,
            signal=MatchSignal.PARTIAL_MATCH,
            confidence=0.5,
        )
        recommendations = generate_recommendations((evaluation,))
        rec = recommendations[0]
        assert rec.type == RecommendationType.EXPERIENCE_CLARIFICATION
        assert rec.safety == RecommendationSafety.REQUIRES_CANDIDATE_CONFIRMATION


class TestConfidenceReflectsEvidenceQuality:
    def test_high_underlying_confidence_yields_high_recommendation_confidence(self):
        evaluation = _evaluation(confidence=0.98)
        assert generate_recommendations((evaluation,))[0].confidence.value == "HIGH"

    def test_low_underlying_confidence_yields_low_recommendation_confidence(self):
        evaluation = _evaluation(
            status=RequirementStatus.UNKNOWN,
            requirement_type=RequirementType.EXPERIENCE,
            confidence=0.3,
        )
        assert generate_recommendations((evaluation,))[0].confidence.value == "LOW"


class TestDeduplicationAndCap:
    def test_identical_type_and_title_are_deduplicated(self):
        evaluation = _evaluation()
        recommendations = generate_recommendations((evaluation, evaluation))
        assert len(recommendations) == 1

    def test_low_priority_items_are_capped_but_critical_items_never_are(self):
        critical = tuple(
            _evaluation(raw_text=f"Skill {i}") for i in range(3)
        )
        low_priority = tuple(
            _evaluation(
                requirement_type=RequirementType.RESPONSIBILITY,
                priority=RequirementPriority.OPTIONAL,
                status=RequirementStatus.NOT_MET,
                raw_text=f"Responsibility {i}",
            )
            for i in range(20)
        )
        recommendations = generate_recommendations(critical + low_priority)
        criticals = [r for r in recommendations if r.priority == RecommendationPriority.CRITICAL]
        assert len(criticals) == 3


class TestSafeToTailorProperty:
    def test_not_safe_to_automate_is_never_safe_to_tailor(self):
        rec = generate_recommendations((_evaluation(),))[0]
        assert rec.safe_to_tailor is False

    def test_safe_to_rephrase_is_safe_to_tailor(self):
        evaluation = _evaluation(
            requirement_type=RequirementType.RESPONSIBILITY,
            priority=RequirementPriority.OPTIONAL,
            status=RequirementStatus.PARTIALLY_MET,
            signal=MatchSignal.SEMANTIC_MATCH,
            confidence=0.7,
        )
        rec = generate_recommendations((evaluation,))[0]
        assert rec.safe_to_tailor is True
