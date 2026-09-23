from application.matching.run_analysis import RunAnalysis
from domain.cv.entities import CandidateProfile, Contact, Experience
from domain.job.entities import JobProfile, JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.matching.enums import AnalysisStatus, MatchSignal
from domain.skills.entities import Skill
from domain.skills.taxonomy import SEED_SKILLS
from infrastructure.embeddings.base import EmbeddingProviderError
from infrastructure.embeddings.providers.fake_provider import FakeEmbeddingProvider


class FakeSkillRepository:
    def all(self):
        return list(SEED_SKILLS)


class FakeCandidateProfileRepository:
    def __init__(self, profile: CandidateProfile | None):
        self._profile = profile

    def get(self, document_id):
        return self._profile


class FakeJobProfileRepository:
    def __init__(self, profile: JobProfile | None):
        self._profile = profile

    def get(self, document_id):
        return self._profile


class FakeAnalysisRepository:
    def __init__(self):
        self.document_pair = ("cv-doc", "job-doc")
        self.processing_marked = False
        self.saved_analysis = None
        self.failure_reason = None

    def get_document_pair(self, analysis_id):
        return self.document_pair

    def mark_processing(self, analysis_id):
        self.processing_marked = True

    def save_result(self, analysis_id, analysis):
        self.saved_analysis = analysis

    def mark_failed(self, analysis_id, error_message):
        self.failure_reason = error_message


class TrackingEmbeddingProvider:
    """Wraps the real, deterministic FakeEmbeddingProvider (different
    text -> different, low-similarity vectors) so these tests exercise
    realistic "no semantic match" behavior, while still tracking whether
    it was called and allowing failure injection.
    """

    def __init__(self, error=None):
        self._delegate = FakeEmbeddingProvider(dimensions=16)
        self._error = error
        self.called = False

    def embed(self, texts):
        self.called = True
        if self._error:
            raise self._error
        return self._delegate.embed(texts)


def _skill(name: str) -> Skill:
    return next(s for s in SEED_SKILLS if s.canonical_name == name)


def _candidate() -> CandidateProfile:
    return CandidateProfile(
        full_name="Jordan Rivera",
        contact=Contact(),
        summary="Backend engineer",
        experiences=(
            Experience(
                title="Senior Backend Engineer",
                company="Acme",
                start_date_raw="2020",
                end_date_raw="Present",
                description="Built REST APIs using Django and PostgreSQL.",
                technologies=("Python", "Django", "PostgreSQL"),
            ),
        ),
    )


def _job(requirements=()) -> JobProfile:
    return JobProfile(
        title="Senior Backend Engineer", company="Acme", location="Remote", employment_type="Full-time",
        seniority="Senior", summary="We are hiring", requirements=requirements,
    )


def _build_use_case(candidate, job, embedding_provider=None, analysis_repository=None):
    analysis_repository = analysis_repository or FakeAnalysisRepository()
    use_case = RunAnalysis(
        candidate_profile_repository=FakeCandidateProfileRepository(candidate),
        job_profile_repository=FakeJobProfileRepository(job),
        skill_repository=FakeSkillRepository(),
        analysis_repository=analysis_repository,
        embedding_provider=embedding_provider or TrackingEmbeddingProvider(),
        engine_version="1.0.0",
    )
    return use_case, analysis_repository


class TestRunAnalysisHappyPath:
    def test_exact_skill_match_produces_a_completed_analysis(self):
        requirement = JobRequirement(
            requirement_type=RequirementType.REQUIRED_SKILL,
            importance=RequirementImportance.REQUIRED,
            raw_text="Django",
            skill=_skill("Django"),
        )
        repository = FakeAnalysisRepository()
        use_case, repository = _build_use_case(
            _candidate(), _job((requirement,)), analysis_repository=repository
        )

        use_case.execute("analysis-1")

        assert repository.processing_marked
        analysis = repository.saved_analysis
        assert analysis.status == AnalysisStatus.COMPLETED
        assert analysis.overall_score is not None
        django_evaluation = next(e for e in analysis.requirement_evaluations if e.raw_text == "Django")
        assert django_evaluation.match_signal == MatchSignal.EXACT_MATCH

    def test_missing_profile_marks_analysis_failed_without_raising(self):
        repository = FakeAnalysisRepository()
        use_case, repository = _build_use_case(None, _job(), analysis_repository=repository)

        use_case.execute("analysis-1")  # must not raise

        assert repository.failure_reason is not None
        assert repository.saved_analysis is None


class TestRunAnalysisSemanticFallback:
    def test_semantic_lookup_only_attempted_when_no_direct_or_related_match(self):
        requirement = JobRequirement(
            requirement_type=RequirementType.REQUIRED_SKILL,
            importance=RequirementImportance.REQUIRED,
            raw_text="Rust",
            skill=_skill("Rust"),
        )
        embedding_provider = TrackingEmbeddingProvider()
        repository = FakeAnalysisRepository()
        use_case, repository = _build_use_case(
            _candidate(),
            _job((requirement,)),
            embedding_provider=embedding_provider,
            analysis_repository=repository,
        )

        use_case.execute("analysis-1")

        assert embedding_provider.called

    def test_embedding_provider_failure_does_not_fail_the_analysis(self):
        requirement = JobRequirement(
            requirement_type=RequirementType.REQUIRED_SKILL,
            importance=RequirementImportance.REQUIRED,
            raw_text="Rust",
            skill=_skill("Rust"),
        )
        embedding_provider = TrackingEmbeddingProvider(error=EmbeddingProviderError("down"))
        repository = FakeAnalysisRepository()
        use_case, repository = _build_use_case(
            _candidate(),
            _job((requirement,)),
            embedding_provider=embedding_provider,
            analysis_repository=repository,
        )

        use_case.execute("analysis-1")  # must not raise

        assert repository.saved_analysis is not None
        assert repository.saved_analysis.status == AnalysisStatus.COMPLETED
        evaluations = repository.saved_analysis.requirement_evaluations
        rust_evaluation = next(e for e in evaluations if e.raw_text == "Rust")
        assert rust_evaluation.match_signal == MatchSignal.NO_EVIDENCE

    def test_embedding_never_attempted_when_exact_match_already_found(self):
        requirement = JobRequirement(
            requirement_type=RequirementType.REQUIRED_SKILL,
            importance=RequirementImportance.REQUIRED,
            raw_text="Django",
            skill=_skill("Django"),
        )
        embedding_provider = TrackingEmbeddingProvider()
        use_case, _ = _build_use_case(
            _candidate(), _job((requirement,)), embedding_provider=embedding_provider
        )

        use_case.execute("analysis-1")

        assert not embedding_provider.called


class TestRunAnalysisMandatoryGaps:
    def test_missing_mandatory_skill_appears_as_a_gap(self):
        requirement = JobRequirement(
            requirement_type=RequirementType.REQUIRED_SKILL,
            importance=RequirementImportance.REQUIRED,
            raw_text="Kubernetes",
            skill=_skill("Kubernetes"),
        )
        repository = FakeAnalysisRepository()
        use_case, repository = _build_use_case(
            _candidate(), _job((requirement,)), analysis_repository=repository
        )

        use_case.execute("analysis-1")

        analysis = repository.saved_analysis
        assert any(gap.raw_text == "Kubernetes" for gap in analysis.gaps)
        assert analysis.score_breakdown.mandatory_gap_penalty > 0.0
