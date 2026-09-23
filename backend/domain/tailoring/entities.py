"""The Tailoring domain model (Phase 5 sections 27, 29, 33-34).

A `TailoringPlan` is inspectable before anything is generated (section
27/28) - the candidate can see exactly which facts will be touched and
which are protected before a single word is rewritten. A `TailoredCV` is
the result of executing that plan: every change carries its own diff and
its own acceptance state, so a rejected proposal (section 57) is visible
rather than silently dropped.
"""
from dataclasses import dataclass, field

from domain.tailoring.enums import ChangeType, TailoringMode, TailoringStatus
from domain.truth.enums import AllowedTransformation, ClaimRejectionReason


@dataclass(frozen=True)
class SectionOperation:
    """One planned edit: which fact, what kind of transformation, and
    which recommendation justified it - the traceable link section 50
    calls "one of the most important UX concepts of Phase 5".
    """

    fact_id: str
    transformation: AllowedTransformation
    recommendation_title: str
    target_state: str | None = None


@dataclass(frozen=True)
class TailoringPlan:
    analysis_id: str
    source_cv_document_id: str
    target_job_document_id: str
    mode: TailoringMode
    engine_version: str
    operations: tuple[SectionOperation, ...] = field(default_factory=tuple)
    protected_fact_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DiffSegment:
    text: str
    change_type: ChangeType


@dataclass(frozen=True)
class TailoringChange:
    fact_id: str
    original_text: str
    final_text: str
    diff: tuple[DiffSegment, ...]
    accepted: bool
    recommendation_title: str
    rejection_reasons: tuple[ClaimRejectionReason, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TailoredCV:
    analysis_id: str
    plan: TailoringPlan
    status: TailoringStatus
    changes: tuple[TailoringChange, ...] = field(default_factory=tuple)
    before_score: float | None = None
    after_score: float | None = None
    requirements_improved: int = 0
    requirements_unchanged: int = 0
    requirements_still_missing: int = 0
    error_message: str | None = None

    @property
    def accepted_changes(self) -> tuple[TailoringChange, ...]:
        return tuple(change for change in self.changes if change.accepted)

    @property
    def rejected_changes(self) -> tuple[TailoringChange, ...]:
        return tuple(change for change in self.changes if not change.accepted)
