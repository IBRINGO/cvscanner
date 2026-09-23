from application.tailoring.run_tailoring import RunTailoring
from domain.cv.entities import CandidateProfile, CandidateSkillMention, Contact, Experience
from domain.job.entities import JobProfile
from domain.skills.entities import Skill
from domain.skills.enums import SkillCategory
from domain.tailoring.entities import SectionOperation, TailoringPlan
from domain.tailoring.enums import TailoringMode, TailoringStatus
from domain.truth.enums import AllowedTransformation
from infrastructure.embeddings.providers.fake_provider import FakeEmbeddingProvider
from infrastructure.llm.providers.fake_provider import FakeLLMProvider


def _skill(name: str) -> Skill:
    return Skill(canonical_name=name, category=SkillCategory.TOOL)


def _candidate() -> CandidateProfile:
    return CandidateProfile(
        full_name="Jordan Rivera",
        contact=Contact(),
        summary=None,
        skills=(CandidateSkillMention(raw_text="Docker", skill=None, evidence=None),),
        experiences=(
            Experience(
                title="Software Engineer",
                company="Northwind Labs",
                start_date_raw="2019",
                end_date_raw="2021",
                description="Built internal tooling for the data platform team.",
                technologies=("Docker",),
                evidence=None,
            ),
        ),
    )


def _job() -> JobProfile:
    return JobProfile(
        title="Senior Backend Engineer",
        company="Acme",
        location=None,
        employment_type=None,
        seniority=None,
        summary=None,
        responsibilities=("Design and maintain REST APIs",),
        requirements=(),
    )


class _FakeTailoringRepository:
    def __init__(self, plan: TailoringPlan):
        self._plan = plan
        self.statuses: list[TailoringStatus] = []
        self.saved_result = None
        self.failed_with: str | None = None

    def get_plan(self, plan_id):
        return self._plan

    def get_analysis_document_pair(self, analysis_id):
        return "cv-1", "job-1"

    def mark_status(self, plan_id, status):
        self.statuses.append(status)

    def mark_failed(self, plan_id, error_message):
        self.failed_with = error_message

    def save_result(self, plan_id, result):
        self.saved_result = result


class _FakeProfileRepository:
    def __init__(self, profile):
        self._profile = profile

    def get(self, document_id):
        return self._profile


class _FakeSkillRepository:
    def __init__(self, skills):
        self._skills = skills

    def all(self):
        return self._skills


def _plan() -> TailoringPlan:
    return TailoringPlan(
        analysis_id="analysis-1",
        source_cv_document_id="cv-1",
        target_job_document_id="job-1",
        mode=TailoringMode.AGGRESSIVE_SAFE,
        engine_version="1.0.0",
        operations=(
            SectionOperation(
                fact_id="experience:0",
                transformation=AllowedTransformation.REPHRASE,
                recommendation_title="Make existing experience match: Design and maintain REST APIs",
            ),
        ),
    )


def _build_use_case(tailoring_repo, llm_provider, skills=None):
    skills = skills if skills is not None else (_skill("Docker"), _skill("Kubernetes"))
    return RunTailoring(
        tailoring_repository=tailoring_repo,
        candidate_profile_repository=_FakeProfileRepository(_candidate()),
        job_profile_repository=_FakeProfileRepository(_job()),
        skill_repository=_FakeSkillRepository(list(skills)),
        embedding_provider=FakeEmbeddingProvider(),
        llm_provider=llm_provider,
    )


class TestRunTailoringSafeRewrite:
    def test_a_safe_rewrite_is_accepted_and_rescored(self):
        repo = _FakeTailoringRepository(_plan())
        rewritten = '{"proposed_text": "Designed and maintained REST APIs for the data platform team."}'
        llm = FakeLLMProvider(response_fn=lambda prompt: rewritten)
        use_case = _build_use_case(repo, llm)

        use_case.execute("plan-1")

        assert repo.failed_with is None
        assert TailoringStatus.PLANNING in repo.statuses
        assert TailoringStatus.GENERATING in repo.statuses
        assert TailoringStatus.VALIDATING in repo.statuses
        result = repo.saved_result
        assert result.status == TailoringStatus.COMPLETED
        assert len(result.changes) == 1
        assert result.changes[0].accepted is True
        assert result.before_score is not None
        assert result.after_score is not None


class TestRunTailoringRejectsHallucination:
    def test_a_hallucinated_kubernetes_claim_is_rejected_and_original_text_kept(self):
        repo = _FakeTailoringRepository(_plan())
        original_description = _candidate().experiences[0].description
        hallucinated = '{"proposed_text": "Managed Kubernetes clusters for the platform team."}'
        llm = FakeLLMProvider(response_fn=lambda prompt: hallucinated)
        use_case = _build_use_case(repo, llm)

        use_case.execute("plan-1")

        result = repo.saved_result
        change = result.changes[0]
        assert change.accepted is False
        assert change.final_text == original_description
        assert len(change.rejection_reasons) >= 1


class TestRunTailoringFailure:
    def test_a_missing_profile_marks_the_plan_failed_not_raised_as_a_bug(self):
        repo = _FakeTailoringRepository(_plan())
        use_case = RunTailoring(
            tailoring_repository=repo,
            candidate_profile_repository=_FakeProfileRepository(None),
            job_profile_repository=_FakeProfileRepository(_job()),
            skill_repository=_FakeSkillRepository([_skill("Docker")]),
            embedding_provider=FakeEmbeddingProvider(),
            llm_provider=FakeLLMProvider(),
        )

        use_case.execute("plan-1")

        assert repo.failed_with is not None
        assert repo.saved_result is None
