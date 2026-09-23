"""Persists a domain JobProfile (+ its embedded Evidence) as Django rows,
and reads one back for Phase 4's matching engine. Mirrors
candidate_profile_repository.py's approach and idempotency (reprocessing
replaces the previous structured data).
"""
from django.db import transaction

from apps.documents.models import Document as DjangoDocument
from apps.documents.models import Evidence as DjangoEvidence
from apps.jobs.models import JobProfile as DjangoJobProfile
from apps.jobs.models import JobRequirement
from apps.skills.models import Skill as DjangoSkill
from domain.cv.seniority import SeniorityLevel
from domain.documents.enums import ExtractionMethod, SectionType
from domain.documents.evidence import Evidence
from domain.job.entities import JobProfile
from domain.job.entities import JobRequirement as DomainJobRequirement
from domain.job.enums import RequirementImportance, RequirementType
from infrastructure.database.repositories.skill_repository import DjangoSkillRepository


class DjangoJobProfileRepository:
    def get(self, document_id: str) -> JobProfile | None:
        row = (
            DjangoJobProfile.objects.filter(document_id=document_id)
            .prefetch_related("requirements__evidence", "requirements__skill")
            .first()
        )
        if row is None:
            return None

        skill_repository = DjangoSkillRepository()
        return JobProfile(
            title=row.title,
            company=row.company,
            location=row.location,
            employment_type=row.employment_type,
            seniority=row.seniority,
            summary=row.summary,
            seniority_normalized=(
                SeniorityLevel(row.seniority_normalized) if row.seniority_normalized else None
            ),
            responsibilities=tuple(row.responsibilities),
            requirements=tuple(
                _requirement_from_row(requirement, skill_repository)
                for requirement in row.requirements.all()
            ),
        )

    @transaction.atomic
    def save(self, document_id: str, profile: JobProfile, document_level_evidence: list[Evidence]) -> None:
        DjangoJobProfile.objects.filter(document_id=document_id).delete()

        row = DjangoJobProfile.objects.create(
            document_id=document_id,
            title=profile.title,
            company=profile.company,
            location=profile.location,
            employment_type=profile.employment_type,
            seniority=profile.seniority,
            summary=profile.summary,
            responsibilities=list(profile.responsibilities),
        )

        for requirement in profile.requirements:
            JobRequirement.objects.create(
                job_profile=row,
                requirement_type=requirement.requirement_type.value,
                importance=requirement.importance.value,
                raw_text=requirement.raw_text,
                skill=_resolve_skill(requirement.skill),
                evidence=_persist_evidence(document_id, requirement.evidence),
            )

        for evidence in document_level_evidence:
            _persist_evidence(document_id, evidence)


def _persist_evidence(document_id: str, evidence: Evidence | None) -> DjangoEvidence | None:
    if evidence is None:
        return None
    return DjangoEvidence.objects.create(
        source_document=DjangoDocument(id=document_id),
        page_number=evidence.page_number,
        section=evidence.section.value if evidence.section else None,
        text=evidence.text,
        start_offset=evidence.start_offset,
        end_offset=evidence.end_offset,
        confidence=evidence.confidence,
        extraction_method=evidence.extraction_method.value,
        metadata=evidence.metadata,
    )


def _resolve_skill(skill) -> DjangoSkill | None:
    if skill is None:
        return None
    return DjangoSkill.objects.filter(canonical_name=skill.canonical_name).first()


def _evidence_from_row(row: DjangoEvidence | None) -> Evidence | None:
    if row is None:
        return None
    return Evidence(
        source_document_id=str(row.source_document_id),
        text=row.text,
        extraction_method=ExtractionMethod(row.extraction_method),
        confidence=row.confidence,
        page_number=row.page_number,
        section=SectionType(row.section) if row.section else None,
        start_offset=row.start_offset,
        end_offset=row.end_offset,
        metadata=row.metadata,
    )


def _requirement_from_row(
    row: JobRequirement, skill_repository: DjangoSkillRepository
) -> DomainJobRequirement:
    return DomainJobRequirement(
        requirement_type=RequirementType(row.requirement_type),
        importance=RequirementImportance(row.importance),
        raw_text=row.raw_text,
        skill=skill_repository.get_by_name(row.skill.canonical_name) if row.skill else None,
        minimum_years=row.minimum_years,
        normalized_value=row.normalized_value,
        evidence=_evidence_from_row(row.evidence),
    )


class DjangoJobEnrichmentRepository:
    """Applies Phase 3 semantic enrichment on top of rows Phase 2 already
    persisted - see DjangoCandidateEnrichmentRepository's docstring in
    candidate_profile_repository.py for why matching by creation order is
    safe here.
    """

    @transaction.atomic
    def apply_seniority(self, document_id: str, seniority_normalized: str | None) -> None:
        DjangoJobProfile.objects.filter(document_id=document_id).update(
            seniority_normalized=seniority_normalized
        )

    @transaction.atomic
    def apply_requirement_enrichment(self, document_id: str, updates: list[dict]) -> None:
        rows = list(JobRequirement.objects.filter(job_profile__document_id=document_id).order_by("id"))
        for row, update in zip(rows, updates, strict=True):
            row.minimum_years = update.get("minimum_years")
            row.normalized_value = update.get("normalized_value")
            row.save(update_fields=["minimum_years", "normalized_value"])
