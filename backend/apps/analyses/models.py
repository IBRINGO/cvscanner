"""Persistence models for the analyses app: the ATS Analysis Phase 4
produces from a CandidateProfile + JobProfile pair (see
domain/matching/entities.py::ATSAnalysis for the framework-free
equivalent these mirror, and
docs/architecture/phase-4-matching.md for the pipeline).

Two tables, not four: `RequirementEvaluation.evidence` and
`Analysis.gaps` are stored as JSON rather than their own related tables.
Both are read-only, presentation-shaped summaries with nothing else ever
pointing at them by foreign key - the relational independence a separate
table buys is not needed here, and it keeps the schema proportional
(section 64 of the Phase 4 brief: "avoid unnecessary indexes"). Evidence
here is a content snapshot (text/page/section/confidence/method), not a
foreign key to the original `documents.Evidence` row it was drawn from -
by the time the matching engine produces a `MatchEvidence`, the domain
layer only carries that row's content, never its database id (the
domain must not know about database ids at all - see
docs/architecture/dependency-rule.md).
"""
import uuid

from django.db import models

from domain.job.enums import RequirementType
from domain.matching.enums import (
    AnalysisStatus,
    MatchSignal,
    MatchStrength,
    RequirementPriority,
    RequirementStatus,
)


class Analysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidate_document = models.ForeignKey(
        "documents.Document", on_delete=models.CASCADE, related_name="analyses_as_candidate"
    )
    job_document = models.ForeignKey(
        "documents.Document", on_delete=models.CASCADE, related_name="analyses_as_job"
    )
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.value) for s in AnalysisStatus],
        default=AnalysisStatus.PENDING.value,
    )
    engine_version = models.CharField(max_length=20)
    overall_score = models.FloatField(null=True, blank=True)
    score_breakdown = models.JSONField(null=True, blank=True)
    gaps = models.JSONField(default=list, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["candidate_document", "job_document"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]
        verbose_name_plural = "analyses"

    def __str__(self) -> str:  # pragma: no cover
        return f"Analysis({self.id}, {self.status})"


class RequirementEvaluationRecord(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="requirement_evaluations")
    requirement_type = models.CharField(max_length=20, choices=[(t.value, t.value) for t in RequirementType])
    priority = models.CharField(max_length=16, choices=[(p.value, p.value) for p in RequirementPriority])
    raw_text = models.CharField(max_length=300)
    status = models.CharField(max_length=16, choices=[(s.value, s.value) for s in RequirementStatus])
    match_signal = models.CharField(max_length=16, choices=[(s.value, s.value) for s in MatchSignal])
    match_strength = models.CharField(max_length=16, choices=[(s.value, s.value) for s in MatchStrength])
    score = models.FloatField()
    confidence = models.FloatField()
    matched_skill = models.CharField(max_length=100, null=True, blank=True)
    explanation = models.TextField(blank=True)
    evidence = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  # pragma: no cover
        return f"RequirementEvaluationRecord({self.raw_text!r}, {self.status})"
