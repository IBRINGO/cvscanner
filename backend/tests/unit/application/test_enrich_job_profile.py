from application.semantics.enrich_job_profile import EnrichJobProfile
from domain.job.entities import JobProfile, JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.skills.enrichment import TechnologyMentionScanner
from domain.skills.taxonomy import SEED_SKILLS


class FakeJobEnrichmentRepository:
    def __init__(self):
        self.seniority = None
        self.requirement_updates = None

    def apply_seniority(self, document_id, seniority_normalized):
        self.seniority = seniority_normalized

    def apply_requirement_enrichment(self, document_id, updates):
        self.requirement_updates = updates


def _profile(**kwargs) -> JobProfile:
    defaults = dict(
        title=None, company=None, location=None, employment_type=None, seniority=None, summary=None
    )
    defaults.update(kwargs)
    return JobProfile(**defaults)


class TestEnrichJobProfile:
    def test_normalizes_seniority_from_seniority_field(self):
        repository = FakeJobEnrichmentRepository()
        profile = _profile(seniority="Senior")
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichJobProfile(repository).execute("doc-1", profile, scanner)

        assert repository.seniority == "SENIOR"

    def test_falls_back_to_title_when_seniority_field_is_empty(self):
        repository = FakeJobEnrichmentRepository()
        profile = _profile(title="Senior Backend Engineer")
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichJobProfile(repository).execute("doc-1", profile, scanner)

        assert repository.seniority == "SENIOR"

    def test_no_seniority_signal_is_unknown_not_guessed(self):
        repository = FakeJobEnrichmentRepository()
        profile = _profile(title="Backend Engineer")
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichJobProfile(repository).execute("doc-1", profile, scanner)

        assert repository.seniority == "UNKNOWN"

    def test_experience_requirement_gets_minimum_years_and_technology(self):
        repository = FakeJobEnrichmentRepository()
        profile = _profile(
            requirements=(
                JobRequirement(
                    requirement_type=RequirementType.EXPERIENCE,
                    importance=RequirementImportance.REQUIRED,
                    raw_text="5 years of Java development",
                ),
            )
        )
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichJobProfile(repository).execute("doc-1", profile, scanner)

        assert repository.requirement_updates == [{"minimum_years": 5, "normalized_value": "Java"}]

    def test_education_requirement_gets_normalized_level(self):
        repository = FakeJobEnrichmentRepository()
        profile = _profile(
            requirements=(
                JobRequirement(
                    requirement_type=RequirementType.EDUCATION,
                    importance=RequirementImportance.REQUIRED,
                    raw_text="Bachelor's degree in Computer Science",
                ),
            )
        )
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichJobProfile(repository).execute("doc-1", profile, scanner)

        assert repository.requirement_updates == [{"normalized_value": "BACHELOR"}]

    def test_skill_requirement_gets_no_enrichment(self):
        repository = FakeJobEnrichmentRepository()
        profile = _profile(
            requirements=(
                JobRequirement(
                    requirement_type=RequirementType.REQUIRED_SKILL,
                    importance=RequirementImportance.REQUIRED,
                    raw_text="Python",
                ),
            )
        )
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichJobProfile(repository).execute("doc-1", profile, scanner)

        assert repository.requirement_updates == [{}]

    def test_never_compares_requirements_to_a_candidate(self):
        # This use case has no candidate parameter at all - the API
        # itself enforces the section 19/25 scope boundary.
        import inspect

        signature = inspect.signature(EnrichJobProfile.execute)
        assert "candidate" not in signature.parameters
