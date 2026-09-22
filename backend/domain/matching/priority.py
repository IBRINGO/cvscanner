"""Maps Phase 2/3's `RequirementImportance` (REQUIRED/PREFERRED) onto
Phase 4's three-tier `RequirementPriority` (section 18 of the brief).

Deliberately does NOT change `domain.job.enums.RequirementImportance` -
that enum is Phase 2's classification of what the extractor read from the
document text and is already relied on by the extraction pipeline and its
tests. `OPTIONAL` has no Phase 2/3 extraction path today (nothing
currently classifies a requirement as merely "optional" rather than
required/preferred); it exists in `RequirementPriority` so the scoring
engine's weighting logic is complete and future extraction work can
populate it without another schema change here.
"""
from domain.job.enums import RequirementImportance
from domain.matching.enums import RequirementPriority

_IMPORTANCE_TO_PRIORITY: dict[RequirementImportance, RequirementPriority] = {
    RequirementImportance.REQUIRED: RequirementPriority.MANDATORY,
    RequirementImportance.PREFERRED: RequirementPriority.PREFERRED,
}


def priority_from_importance(importance: RequirementImportance) -> RequirementPriority:
    return _IMPORTANCE_TO_PRIORITY[importance]
