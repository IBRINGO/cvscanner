"""Document ingestion/parsing bounded context.

Added in Phase 2. Not anticipated by name in the Phase 1 domain module
list (cv, candidate, job, skills, matching, scoring, recommendations,
tailoring) because "a document being ingested and parsed" is a distinct
concept from "a CV" or "a job offer" - both CVs and job offers are
Documents first, before either becomes a CandidateProfile or JobProfile.

See docs/architecture/dependency-rule.md for the rule this module must
keep following: no Django, Celery, or vendor SDK imports here.
"""
