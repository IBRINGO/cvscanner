"""Versioning for the Tailoring Engine (Phase 5 section 78). Persisted on
every `TailoringPlan`/`TailoredCV` so historical tailored CVs stay
auditable against the exact planning/validation logic that produced
them, independent of the matching engine's own `MATCHING_ENGINE_VERSION`
and the Truth Layer's `TRUTH_LAYER_VERSION`.
"""

TAILORING_ENGINE_VERSION = "1.0.0"
