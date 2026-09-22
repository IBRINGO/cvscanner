from domain.job.enums import RequirementType
from domain.matching.engine import compute_score_breakdown, detect_gaps
from domain.matching.entities import RequirementEvaluation
from domain.matching.enums import MatchSignal, MatchStrength, RequirementPriority, RequirementStatus
from domain.matching.weights import MatchingWeights


def _evaluation(
    priority=RequirementPriority.PREFERRED,
    status=RequirementStatus.MET,
    score=1.0,
    signal=MatchSignal.EXACT_MATCH,
    matched_skill=None,
) -> RequirementEvaluation:
    return RequirementEvaluation(
        requirement_type=RequirementType.REQUIRED_SKILL,
        priority=priority,
        raw_text="Django",
        status=status,
        match_signal=signal,
        match_strength=MatchStrength.STRONG,
        score=score,
        confidence=0.9,
        matched_skill=matched_skill,
    )


def _missing_mandatory() -> RequirementEvaluation:
    return _evaluation(
        priority=RequirementPriority.MANDATORY,
        status=RequirementStatus.NOT_MET,
        score=0.0,
        signal=MatchSignal.NO_EVIDENCE,
    )


class TestComputeScoreBreakdown:
    def test_full_marks_across_all_dimensions(self):
        full = (_evaluation(),)
        breakdown = compute_score_breakdown(
            skills=full, experience=full, seniority=full, education=full,
            certifications=full, languages=full, responsibilities=full, domain=full,
        )
        assert breakdown.overall == 1.0

    def test_missing_dimension_is_excluded_not_zeroed(self):
        full = (_evaluation(),)
        empty: tuple = ()
        breakdown = compute_score_breakdown(
            skills=full, experience=full, seniority=full, education=full,
            certifications=empty, languages=empty, responsibilities=full, domain=full,
        )
        # Overall should still be 1.0 - certifications/languages had no
        # requirements at all, so they must not drag the score down.
        assert breakdown.overall == 1.0
        # Reported as 0 for display, but excluded from the weighted average.
        assert breakdown.certifications == 0.0

    def test_mandatory_gap_reduces_overall_but_does_not_zero_it(self):
        met = (_evaluation(),)
        missing_mandatory = (_missing_mandatory(),)
        breakdown = compute_score_breakdown(
            skills=missing_mandatory, experience=met, seniority=met, education=met,
            certifications=met, languages=met, responsibilities=met, domain=met,
        )
        assert breakdown.overall > 0.0
        assert breakdown.overall < 1.0
        assert breakdown.mandatory_gap_penalty > 0.0

    def test_penalty_is_capped(self):
        many_missing = tuple(_missing_mandatory() for _ in range(10))
        weights = MatchingWeights()
        breakdown = compute_score_breakdown(
            skills=many_missing, experience=(), seniority=(), education=(),
            certifications=(), languages=(), responsibilities=(), domain=(),
        )
        assert breakdown.mandatory_gap_penalty == weights.mandatory_penalty_cap

    def test_no_evaluations_anywhere_is_zero_not_an_error(self):
        empty: tuple = ()
        breakdown = compute_score_breakdown(
            skills=empty, experience=empty, seniority=empty, education=empty,
            certifications=empty, languages=empty, responsibilities=empty, domain=empty,
        )
        assert breakdown.overall == 0.0

    def test_weights_must_sum_to_one(self):
        import pytest

        with pytest.raises(ValueError):
            MatchingWeights(skills=0.9, experience=0.9)


class TestDetectGaps:
    def test_not_met_produces_a_gap(self):
        evaluations = (_missing_mandatory(),)
        gaps = detect_gaps(evaluations)
        assert len(gaps) == 1
        assert gaps[0].evidence_status == "NO_EVIDENCE"

    def test_met_produces_no_gap(self):
        evaluations = (_evaluation(status=RequirementStatus.MET),)
        assert detect_gaps(evaluations) == ()

    def test_partial_evidence_gap_is_distinguished_from_no_evidence(self):
        evaluation = RequirementEvaluation(
            requirement_type=RequirementType.REQUIRED_SKILL,
            priority=RequirementPriority.MANDATORY,
            raw_text="Kubernetes",
            status=RequirementStatus.PARTIALLY_MET,
            match_signal=MatchSignal.RELATED_MATCH,
            match_strength=MatchStrength.PARTIAL,
            score=0.5,
            confidence=0.8,
            matched_skill="Docker",
            evidence=(),
        )
        gaps = detect_gaps((evaluation,))
        assert gaps[0].evidence_status == "PARTIAL_EVIDENCE"
        assert gaps[0].related_candidate_skills == ("Docker",)
