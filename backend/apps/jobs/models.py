"""Persistence models for the jobs app: the structured JobProfile
produced by job-offer extraction (sections 21-23 of the Phase 2 brief).
No candidate comparison lives here - see domain/job/entities.py.
"""
from django.db import models

from domain.job.enums import RequirementImportance, RequirementType


class JobProfile(models.Model):
    document = models.OneToOneField(
        "documents.Document", on_delete=models.CASCADE, related_name="job_profile"
    )
    title = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    employment_type = models.CharField(max_length=50, null=True, blank=True)
    seniority = models.CharField(max_length=50, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    responsibilities = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.title or f"JobProfile({self.document_id})"


class JobRequirement(models.Model):
    job_profile = models.ForeignKey(JobProfile, on_delete=models.CASCADE, related_name="requirements")
    requirement_type = models.CharField(
        max_length=20, choices=[(t.value, t.value) for t in RequirementType]
    )
    importance = models.CharField(
        max_length=16, choices=[(i.value, i.value) for i in RequirementImportance]
    )
    raw_text = models.CharField(max_length=300)
    skill = models.ForeignKey(
        "skills.Skill", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    evidence = models.ForeignKey(
        "documents.Evidence", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["id"]
