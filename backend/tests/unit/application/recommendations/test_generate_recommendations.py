from application.recommendations.generate_recommendations import GenerateRecommendations
from domain.job.enums import RequirementType
from domain.matching.entities import RequirementEvaluation
from domain.matching.enums import MatchSignal, MatchStrength, RequirementPriority, RequirementStatus


def _evaluation() -> RequirementEvaluation:
    return RequirementEvaluation(
        requirement_type=RequirementType.REQUIRED_SKILL,
        priority=RequirementPriority.MANDATORY,
        raw_text="Kubernetes",
        status=RequirementStatus.NOT_MET,
        match_signal=MatchSignal.NO_EVIDENCE,
        match_strength=MatchStrength.NONE,
        score=0.0,
        confidence=0.9,
        explanation="No evidence of Kubernetes.",
    )


class _FakeAnalysisRepository:
    def __init__(self, evaluations):
        self._evaluations = evaluations
        self.calls = 0

    def get_requirement_evaluations(self, analysis_id):
        self.calls += 1
        return self._evaluations


class _FakeRecommendationRepository:
    def __init__(self):
        self._store = {}
        self.save_calls = 0

    def get_for_analysis(self, analysis_id, engine_version):
        return self._store.get((analysis_id, engine_version))

    def save(self, analysis_id, engine_version, recommendations):
        self.save_calls += 1
        self._store[(analysis_id, engine_version)] = recommendations


class TestGenerateRecommendations:
    def test_computes_and_persists_on_first_call(self):
        analysis_repo = _FakeAnalysisRepository((_evaluation(),))
        rec_repo = _FakeRecommendationRepository()
        use_case = GenerateRecommendations(analysis_repo, rec_repo, engine_version="1.0.0")

        result = use_case.execute("analysis-1")

        assert len(result) == 1
        assert rec_repo.save_calls == 1
        assert analysis_repo.calls == 1

    def test_second_call_reuses_the_persisted_result_without_recomputing(self):
        analysis_repo = _FakeAnalysisRepository((_evaluation(),))
        rec_repo = _FakeRecommendationRepository()
        use_case = GenerateRecommendations(analysis_repo, rec_repo, engine_version="1.0.0")

        use_case.execute("analysis-1")
        use_case.execute("analysis-1")

        assert rec_repo.save_calls == 1
        assert analysis_repo.calls == 1
