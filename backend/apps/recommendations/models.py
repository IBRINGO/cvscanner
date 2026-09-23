"""Persistence models for the recommendations app: the deterministic,
evidence-backed findings Phase 5's recommendation engine produces from
an already-completed `Analysis` (see domain/recommendations/entities.py
for the framework-free equivalent, and
docs/architecture/phase-5-recommendations-and-tailoring.md).

One table, not two: a `RecommendationEvidence` table was considered and
rejected the same way Phase 4 rejected a separate evidence table for
`RequirementEvaluationRecord` (see apps/analyses/models.py's module
docstring) - `supporting_evidence` is a read-only content snapshot
copied from the originating `RequirementEvaluationRecord.evidence`, not
an independent fact with its own lifecycle.
"""
import uuid

from django.db import models

from domain.recommendations.enums import (
    RecommendationConfidence,
    RecommendationImpact,
    RecommendationPriority,
    RecommendationSafety,
    RecommendationType,
)


class Recommendation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(
        "analyses.Analysis", on_delete=models.CASCADE, related_name="recommendations"
    )
    engine_version = models.CharField(max_length=20)
    type = models.CharField(max_length=32, choices=[(t.value, t.value) for t in RecommendationType])
    priority = models.CharField(max_length=16, choices=[(p.value, p.value) for p in RecommendationPriority])
    confidence = models.CharField(
        max_length=16, choices=[(c.value, c.value) for c in RecommendationConfidence]
    )
    safety = models.CharField(max_length=32, choices=[(s.value, s.value) for s in RecommendationSafety])
    impact = models.CharField(max_length=16, choices=[(i.value, i.value) for i in RecommendationImpact])
    title = models.CharField(max_length=300)
    summary = models.TextField()
    reason = models.TextField()
    suggested_action = models.TextField()
    related_requirement = models.ForeignKey(
        "analyses.RequirementEvaluationRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    supporting_evidence = models.JSONField(default=list, blank=True)
    current_state = models.CharField(max_length=200, null=True, blank=True)
    target_state = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["analysis"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"Recommendation({self.title!r}, {self.priority})"
