"""Persistence models for the candidates app: the structured
CandidateProfile produced by CV extraction (sections 14-19 of the Phase 2
brief). See domain/cv/entities.py for the framework-free equivalents
these mirror.
"""
from django.db import models


class CandidateProfile(models.Model):
    document = models.OneToOneField(
        "documents.Document", on_delete=models.CASCADE, related_name="candidate_profile"
    )
    full_name = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=40, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    links = models.JSONField(default=list, blank=True)
    summary = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover
        return self.full_name or f"CandidateProfile({self.document_id})"


class Experience(models.Model):
    candidate_profile = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, related_name="experiences"
    )
    title = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    start_date_raw = models.CharField(max_length=50, null=True, blank=True)
    end_date_raw = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    achievements = models.JSONField(default=list, blank=True)
    technologies = models.JSONField(default=list, blank=True)
    evidence = models.ForeignKey(
        "documents.Evidence", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["id"]


class Education(models.Model):
    candidate_profile = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, related_name="education"
    )
    institution = models.CharField(max_length=200, null=True, blank=True)
    degree = models.CharField(max_length=200, null=True, blank=True)
    field_of_study = models.CharField(max_length=200, null=True, blank=True)
    start_date_raw = models.CharField(max_length=50, null=True, blank=True)
    end_date_raw = models.CharField(max_length=50, null=True, blank=True)
    evidence = models.ForeignKey(
        "documents.Evidence", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["id"]
        verbose_name_plural = "education"


class Project(models.Model):
    candidate_profile = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    technologies = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["id"]


class Certification(models.Model):
    candidate_profile = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, related_name="certifications"
    )
    name = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200, null=True, blank=True)
    date_raw = models.CharField(max_length=50, null=True, blank=True)
    evidence = models.ForeignKey(
        "documents.Evidence", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["id"]


class Language(models.Model):
    candidate_profile = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, related_name="languages"
    )
    name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ["id"]


class CandidateSkill(models.Model):
    candidate_profile = models.ForeignKey(
        CandidateProfile, on_delete=models.CASCADE, related_name="skills"
    )
    skill = models.ForeignKey(
        "skills.Skill", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    raw_text = models.CharField(max_length=200)
    evidence = models.ForeignKey(
        "documents.Evidence", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["id"]
