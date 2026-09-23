"""Persistence models for the tailoring app: the plan-then-generate
workflow Phase 5's Tailoring Engine runs against an `Analysis`'s
selected `Recommendation`s (see domain/tailoring/entities.py for the
framework-free equivalents, and
docs/architecture/phase-5-recommendations-and-tailoring.md).

Two tables, not four. `TailoringPlan` folds what the brief calls
"TailoredCV" into itself (status/before_score/after_score/requirement
deltas) rather than a separate row - a tailoring run IS its plan, plus
the outcome of executing it; there is no independent "tailored CV"
identity beyond one plan's result. `TailoringChange` folds what the
brief calls "TailoredSection" into itself (original/final text, diff,
acceptance) - a change record already IS a validated (or rejected)
section proposal; keeping them as one row avoids a table whose only
relationship is a required one-to-one with `TailoringChange`, the same
"avoid unnecessary tables/indexes" discipline
apps/analyses/models.py's docstring documents for Phase 4.
"""
import uuid

from django.db import models

from domain.tailoring.enums import TailoringMode, TailoringStatus


class TailoringPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(
        "analyses.Analysis", on_delete=models.CASCADE, related_name="tailoring_plans"
    )
    mode = models.CharField(max_length=20, choices=[(m.value, m.value) for m in TailoringMode])
    engine_version = models.CharField(max_length=20)
    status = models.CharField(
        max_length=16,
        choices=[(s.value, s.value) for s in TailoringStatus],
        default=TailoringStatus.PENDING.value,
    )
    operations = models.JSONField(default=list, blank=True)
    protected_fact_ids = models.JSONField(default=list, blank=True)
    before_score = models.FloatField(null=True, blank=True)
    after_score = models.FloatField(null=True, blank=True)
    requirements_improved = models.IntegerField(default=0)
    requirements_unchanged = models.IntegerField(default=0)
    requirements_still_missing = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["analysis"]), models.Index(fields=["status"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"TailoringPlan({self.id}, {self.status})"


class TailoringChange(models.Model):
    plan = models.ForeignKey(TailoringPlan, on_delete=models.CASCADE, related_name="changes")
    fact_id = models.CharField(max_length=100)
    recommendation_title = models.CharField(max_length=300)
    original_text = models.TextField()
    final_text = models.TextField()
    diff = models.JSONField(default=list, blank=True)
    accepted = models.BooleanField()
    rejection_reasons = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:  # pragma: no cover
        return f"TailoringChange({self.fact_id!r}, accepted={self.accepted})"
