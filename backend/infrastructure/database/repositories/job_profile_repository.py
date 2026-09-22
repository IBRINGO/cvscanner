"""Persists a domain JobProfile (+ its embedded Evidence) as Django rows.
Mirrors candidate_profile_repository.py's approach and idempotency
(reprocessing replaces the previous structured data).
"""
from django.db import transaction

from apps.documents.models import Document as DjangoDocument
from apps.documents.models import Evidence as DjangoEvidence
from apps.jobs.models import JobProfile as DjangoJobProfile
from apps.jobs.models import JobRequirement
from apps.skills.models import Skill as DjangoSkill
from domain.documents.evidence import Evidence
from domain.job.entities import JobProfile


class DjangoJobProfileRepository:
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
