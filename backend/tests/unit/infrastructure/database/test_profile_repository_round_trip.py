"""Phase 4 needs to read back the enriched CandidateProfile/JobProfile
domain objects the matching engine consumes - these tests confirm
save() -> get() round-trips correctly, including Phase 3's enrichment
fields, which Phase 2's original tests never exercised in this direction.
"""
import uuid

import pytest

from apps.documents.models import Document
from domain.cv.entities import CandidateProfile, CandidateSkillMention, Contact, Experience
from domain.documents.enums import DocumentType, ExtractionMethod
from domain.documents.evidence import Evidence
from domain.job.entities import JobProfile, JobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from domain.skills.entities import Skill
from domain.skills.enums import SkillCategory
from infrastructure.database.repositories.candidate_profile_repository import (
    DjangoCandidateProfileRepository,
)
from infrastructure.database.repositories.job_profile_repository import DjangoJobProfileRepository

pytestmark = pytest.mark.django_db


def _evidence(document_id: str, text: str) -> Evidence:
    return Evidence(
        source_document_id=document_id, text=text, extraction_method=ExtractionMethod.RULE, confidence=0.9
    )


def _make_document(document_type: DocumentType, file_hash: str) -> Document:
    return Document.objects.create(
        document_type=document_type.value,
        original_filename="fixture.pdf",
        mime_type="application/pdf",
        file_size=10,
        file_hash=file_hash,
        storage_reference="fixture/fixture.pdf",
    )


class TestCandidateProfileRoundTrip:
    def test_get_reconstructs_experience_with_enrichment_fields(self):
        document = _make_document(DocumentType.CV, "a" * 64)
        document_id = str(document.id)
        profile = CandidateProfile(
            full_name="Ada Lovelace",
            contact=Contact(email="ada@example.com"),
            summary="Engineer",
            experiences=(
                Experience(
                    title="Senior Backend Engineer",
                    company="Acme",
                    start_date_raw="2020",
                    end_date_raw="Present",
                    description="Built APIs",
                    technologies=("Python", "Django"),
                    evidence=_evidence(document_id, "Senior Backend Engineer at Acme"),
                ),
            ),
            skills=(
                CandidateSkillMention(
                    raw_text="Django",
                    skill=Skill("Django", SkillCategory.FRAMEWORK),
                    evidence=_evidence(document_id, "Django"),
                ),
            ),
        )
        repository = DjangoCandidateProfileRepository()
        repository.save(document_id, profile, [])

        from infrastructure.database.repositories.candidate_profile_repository import (
            DjangoCandidateEnrichmentRepository,
        )

        DjangoCandidateEnrichmentRepository().apply_experience_enrichment(
            document_id, [{"seniority": "SENIOR", "technologies": ["Python", "Django"]}]
        )

        loaded = repository.get(document_id)

        assert loaded is not None
        assert loaded.full_name == "Ada Lovelace"
        assert loaded.experiences[0].seniority == "SENIOR"
        assert loaded.experiences[0].technologies == ("Python", "Django")
        assert loaded.experiences[0].evidence.text == "Senior Backend Engineer at Acme"
        assert loaded.skills[0].skill.canonical_name == "Django"

    def test_get_returns_none_for_unknown_document(self):
        assert DjangoCandidateProfileRepository().get(str(uuid.uuid4())) is None


class TestJobProfileRoundTrip:
    def test_get_reconstructs_requirement_with_full_skill_and_enrichment(self):
        document = _make_document(DocumentType.JOB_OFFER, "b" * 64)
        document_id = str(document.id)
        profile = JobProfile(
            title="Senior Backend Engineer",
            company="Acme",
            location="Remote",
            employment_type="Full-time",
            seniority="Senior",
            summary="We are hiring",
            requirements=(
                JobRequirement(
                    requirement_type=RequirementType.REQUIRED_SKILL,
                    importance=RequirementImportance.REQUIRED,
                    raw_text="Django",
                    skill=Skill("Django", SkillCategory.FRAMEWORK, parent_skill="Python"),
                    evidence=_evidence(document_id, "Django"),
                ),
                JobRequirement(
                    requirement_type=RequirementType.EXPERIENCE,
                    importance=RequirementImportance.REQUIRED,
                    raw_text="5 years of Python",
                    evidence=_evidence(document_id, "5 years of Python"),
                ),
            ),
        )
        repository = DjangoJobProfileRepository()
        repository.save(document_id, profile, [])

        from infrastructure.database.repositories.job_profile_repository import (
            DjangoJobEnrichmentRepository,
        )

        DjangoJobEnrichmentRepository().apply_seniority(document_id, "SENIOR")
        DjangoJobEnrichmentRepository().apply_requirement_enrichment(
            document_id, [{}, {"minimum_years": 5, "normalized_value": "Python"}]
        )

        loaded = repository.get(document_id)

        assert loaded is not None
        assert loaded.seniority_normalized == "SENIOR"
        django_requirement = loaded.requirements[0]
        assert django_requirement.skill.canonical_name == "Django"
        assert django_requirement.skill.parent_skill == "Python"  # full skill, not a stub
        experience_requirement = loaded.requirements[1]
        assert experience_requirement.minimum_years == 5
        assert experience_requirement.normalized_value == "Python"

    def test_get_returns_none_for_unknown_document(self):
        assert DjangoJobProfileRepository().get(str(uuid.uuid4())) is None
