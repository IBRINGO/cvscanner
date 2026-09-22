"""Persists a domain CandidateProfile (+ its embedded Evidence) as
Django rows. One CandidateProfile per Document (OneToOne) - re-saving
(reprocessing) replaces the previous structured data, matching the
idempotency approach documented in
docs/architecture/phase-2-pipeline.md#idempotency.
"""
from django.db import transaction

from apps.candidates.models import CandidateProfile as DjangoCandidateProfile
from apps.candidates.models import (
    CandidateSkill,
    Certification,
    Education,
    Experience,
    Language,
    Project,
)
from apps.documents.models import Document as DjangoDocument
from apps.documents.models import Evidence as DjangoEvidence
from apps.skills.models import Skill as DjangoSkill
from domain.cv.entities import CandidateProfile
from domain.documents.evidence import Evidence


class DjangoCandidateProfileRepository:
    @transaction.atomic
    def save(
        self, document_id: str, profile: CandidateProfile, document_level_evidence: list[Evidence]
    ) -> None:
        DjangoCandidateProfile.objects.filter(document_id=document_id).delete()

        row = DjangoCandidateProfile.objects.create(
            document_id=document_id,
            full_name=profile.full_name,
            email=profile.contact.email,
            phone=profile.contact.phone,
            location=profile.contact.location,
            links=list(profile.contact.links),
            summary=profile.summary,
        )

        for experience in profile.experiences:
            Experience.objects.create(
                candidate_profile=row,
                title=experience.title,
                company=experience.company,
                start_date_raw=experience.start_date_raw,
                end_date_raw=experience.end_date_raw,
                description=experience.description,
                achievements=list(experience.achievements),
                technologies=list(experience.technologies),
                evidence=_persist_evidence(document_id, experience.evidence),
            )

        for education in profile.education:
            Education.objects.create(
                candidate_profile=row,
                institution=education.institution,
                degree=education.degree,
                field_of_study=education.field_of_study,
                start_date_raw=education.start_date_raw,
                end_date_raw=education.end_date_raw,
                evidence=_persist_evidence(document_id, education.evidence),
            )

        for project in profile.projects:
            Project.objects.create(
                candidate_profile=row,
                name=project.name,
                description=project.description,
                technologies=list(project.technologies),
            )

        for certification in profile.certifications:
            Certification.objects.create(
                candidate_profile=row,
                name=certification.name,
                issuer=certification.issuer,
                date_raw=certification.date_raw,
                evidence=_persist_evidence(document_id, certification.evidence),
            )

        for language in profile.languages:
            Language.objects.create(
                candidate_profile=row, name=language.name, proficiency=language.proficiency
            )

        for skill_mention in profile.skills:
            CandidateSkill.objects.create(
                candidate_profile=row,
                skill=_resolve_skill(skill_mention.skill),
                raw_text=skill_mention.raw_text,
                evidence=_persist_evidence(document_id, skill_mention.evidence),
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


class DjangoCandidateEnrichmentRepository:
    """Applies Phase 3 semantic enrichment on top of rows Phase 2 already
    persisted (see DjangoCandidateProfileRepository.save() above).

    Matches enrichment values to rows by creation order (`ordering =
    ["id"]` on each model, same order `save()` iterated the domain
    profile's tuples in) rather than by any business key, because
    Experience/Education/Language rows have none - this is safe because
    enrichment always runs immediately after save() in the same pipeline
    execution, before anything else can touch these rows.
    """

    @transaction.atomic
    def apply_experience_enrichment(self, document_id: str, updates: list[dict]) -> None:
        rows = list(Experience.objects.filter(candidate_profile__document_id=document_id).order_by("id"))
        for row, update in zip(rows, updates, strict=True):
            row.seniority = update.get("seniority")
            row.technologies = update.get("technologies", row.technologies)
            row.save(update_fields=["seniority", "technologies"])

    @transaction.atomic
    def apply_education_enrichment(self, document_id: str, updates: list[dict]) -> None:
        rows = list(Education.objects.filter(candidate_profile__document_id=document_id).order_by("id"))
        for row, update in zip(rows, updates, strict=True):
            row.degree_level = update.get("degree_level")
            row.save(update_fields=["degree_level"])

    @transaction.atomic
    def apply_language_enrichment(self, document_id: str, updates: list[dict]) -> None:
        rows = list(Language.objects.filter(candidate_profile__document_id=document_id).order_by("id"))
        for row, update in zip(rows, updates, strict=True):
            row.canonical_name = update.get("canonical_name")
            row.proficiency_normalized = update.get("proficiency_normalized")
            row.save(update_fields=["canonical_name", "proficiency_normalized"])
