from application.semantics.enrich_candidate_profile import EnrichCandidateProfile
from domain.cv.entities import CandidateProfile, Contact, Education, Experience, Language
from domain.skills.enrichment import TechnologyMentionScanner
from domain.skills.taxonomy import SEED_SKILLS


class FakeCandidateEnrichmentRepository:
    def __init__(self):
        self.experience_updates = None
        self.education_updates = None
        self.language_updates = None

    def apply_experience_enrichment(self, document_id, updates):
        self.experience_updates = updates

    def apply_education_enrichment(self, document_id, updates):
        self.education_updates = updates

    def apply_language_enrichment(self, document_id, updates):
        self.language_updates = updates


class TestEnrichCandidateProfile:
    def test_computes_seniority_from_experience_title(self):
        repository = FakeCandidateEnrichmentRepository()
        profile = CandidateProfile(
            full_name="Ada",
            contact=Contact(),
            summary=None,
            experiences=(
                Experience(
                    title="Senior Software Engineer",
                    company="Acme",
                    start_date_raw=None,
                    end_date_raw=None,
                    description=None,
                ),
            ),
        )
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichCandidateProfile(repository).execute("doc-1", profile, scanner)

        assert repository.experience_updates == [{"seniority": "SENIOR", "technologies": []}]

    def test_merges_prose_technology_mentions_with_explicit_list(self):
        repository = FakeCandidateEnrichmentRepository()
        profile = CandidateProfile(
            full_name=None,
            contact=Contact(),
            summary=None,
            experiences=(
                Experience(
                    title="Backend Engineer",
                    company="Acme",
                    start_date_raw=None,
                    end_date_raw=None,
                    description="Built REST APIs using Django and PostgreSQL.",
                    technologies=("Docker",),
                ),
            ),
        )
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichCandidateProfile(repository).execute("doc-1", profile, scanner)

        update = repository.experience_updates[0]
        assert update["technologies"][0] == "Docker"  # explicit list preserved first
        assert "Django" in update["technologies"]
        assert "PostgreSQL" in update["technologies"]
        assert "REST" in update["technologies"]

    def test_never_equates_django_with_python_in_enrichment(self):
        repository = FakeCandidateEnrichmentRepository()
        profile = CandidateProfile(
            full_name=None,
            contact=Contact(),
            summary=None,
            experiences=(
                Experience(
                    title="Engineer",
                    company=None,
                    start_date_raw=None,
                    end_date_raw=None,
                    description="Developed services with Django.",
                ),
            ),
        )
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichCandidateProfile(repository).execute("doc-1", profile, scanner)

        assert repository.experience_updates[0]["technologies"] == ["Django"]

    def test_normalizes_education_degree_level(self):
        repository = FakeCandidateEnrichmentRepository()
        profile = CandidateProfile(
            full_name=None,
            contact=Contact(),
            summary=None,
            education=(
                Education(
                    institution="MIT",
                    degree="Master of Science",
                    field_of_study="CS",
                    start_date_raw=None,
                    end_date_raw=None,
                ),
            ),
        )
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichCandidateProfile(repository).execute("doc-1", profile, scanner)

        assert repository.education_updates == [{"degree_level": "MASTER"}]

    def test_normalizes_language_name_and_proficiency(self):
        repository = FakeCandidateEnrichmentRepository()
        profile = CandidateProfile(
            full_name=None,
            contact=Contact(),
            summary=None,
            languages=(Language(name="anglais", proficiency="native"),),
        )
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichCandidateProfile(repository).execute("doc-1", profile, scanner)

        assert repository.language_updates == [
            {"canonical_name": "English", "proficiency_normalized": "NATIVE"}
        ]

    def test_no_lists_skips_repository_calls(self):
        repository = FakeCandidateEnrichmentRepository()
        profile = CandidateProfile(full_name=None, contact=Contact(), summary=None)
        scanner = TechnologyMentionScanner(SEED_SKILLS)

        EnrichCandidateProfile(repository).execute("doc-1", profile, scanner)

        assert repository.experience_updates is None
        assert repository.education_updates is None
        assert repository.language_updates is None
