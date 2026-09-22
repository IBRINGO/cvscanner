"""Experience-duration requirement matching (section 11 of the Phase 4
brief). Compares a required "N years" against years the candidate can
actually support - merging overlapping date ranges so two experiences run
concurrently are never double-counted, and never inventing a number when
the source dates cannot be parsed (the requirement stays NO_EVIDENCE with
an honest explanation instead).

Deliberately year-granularity only (`start_date_raw`/`end_date_raw` are
free CV text like "January 2020" or "2013") - this is a coarse but honest
approximation, not a precise day-level calculation.
"""
import re
from dataclasses import dataclass
from datetime import date

from domain.cv.entities import Experience
from domain.job.entities import JobRequirement
from domain.matching.entities import MatchEvidence, RequirementEvaluation
from domain.matching.enums import MatchSignal, RequirementStatus
from domain.matching.priority import priority_from_importance
from domain.matching.strength import SCORE_FOR_STRENGTH, confidence_for_signal, strength_for_signal

_YEAR_RE = re.compile(r"(19|20)\d{2}")
_PRESENT_RE = re.compile(r"present|current|now|ongoing", re.IGNORECASE)


@dataclass(frozen=True)
class ExperienceYearsResult:
    total_years: float | None
    contributing_experiences: tuple[Experience, ...]


def compute_years_of_experience(
    experiences: tuple[Experience, ...],
    technology: str | None = None,
    reference_date: date | None = None,
) -> ExperienceYearsResult:
    reference_year = (reference_date or date.today()).year
    relevant = [
        experience
        for experience in experiences
        if technology is None or technology in experience.technologies
    ]

    if not relevant:
        # No experience even mentions the required technology at all -
        # a confident zero, not an unparseable-date ambiguity.
        return ExperienceYearsResult(total_years=0.0, contributing_experiences=())

    intervals: list[tuple[int, int]] = []
    contributing: list[Experience] = []
    for experience in relevant:
        span = _parse_year_range(experience.start_date_raw, experience.end_date_raw, reference_year)
        if span is not None:
            intervals.append(span)
            contributing.append(experience)

    if not intervals:
        # Relevant experience exists but its dates could not be parsed -
        # a genuine ambiguity (section 11: represent the limitation
        # rather than inventing a number).
        return ExperienceYearsResult(total_years=None, contributing_experiences=())

    merged = _merge_intervals(intervals)
    total_years = float(sum(end - start for start, end in merged))
    return ExperienceYearsResult(total_years=total_years, contributing_experiences=tuple(contributing))


def evaluate_experience_requirement(
    requirement: JobRequirement,
    experiences: tuple[Experience, ...],
    reference_date: date | None = None,
) -> RequirementEvaluation:
    priority = priority_from_importance(requirement.importance)
    required_years = requirement.minimum_years
    result = compute_years_of_experience(experiences, requirement.normalized_value, reference_date)

    if result.total_years is None:
        return _evaluation(
            requirement,
            priority,
            signal=MatchSignal.NO_EVIDENCE,
            status=RequirementStatus.UNKNOWN,
            evidence_experiences=(),
            explanation=(
                "Experience dates could not be determined from the CV, so duration cannot be verified."
            ),
        )

    if required_years is None:
        # The requirement text didn't state a clear number of years (see
        # domain/job/requirement_semantics.py) - we can still confirm the
        # candidate has *some* relevant experience, just not measure it
        # against a target.
        has_evidence = result.total_years > 0
        signal = MatchSignal.PARTIAL_MATCH if has_evidence else MatchSignal.NO_EVIDENCE
        status = RequirementStatus.PARTIALLY_MET if has_evidence else RequirementStatus.NOT_MET
        years = result.total_years
        return _evaluation(
            requirement,
            priority,
            signal=signal,
            status=status,
            evidence_experiences=result.contributing_experiences,
            explanation=f"No specific year count required; candidate shows {years:g} relevant year(s).",
        )

    if result.total_years >= required_years:
        years = result.total_years
        return _evaluation(
            requirement,
            priority,
            signal=MatchSignal.EXACT_MATCH,
            status=RequirementStatus.MET,
            evidence_experiences=result.contributing_experiences,
            explanation=f"Candidate shows {years:g} year(s), meeting the {required_years}-year requirement.",
        )

    if result.total_years > 0:
        years = result.total_years
        return _evaluation(
            requirement,
            priority,
            signal=MatchSignal.PARTIAL_MATCH,
            status=RequirementStatus.PARTIALLY_MET,
            evidence_experiences=result.contributing_experiences,
            explanation=f"Candidate shows {years:g} year(s); the requirement asks for {required_years}.",
        )

    return _evaluation(
        requirement,
        priority,
        signal=MatchSignal.NO_EVIDENCE,
        status=RequirementStatus.NOT_MET,
        evidence_experiences=(),
        explanation=f"No experience found matching this requirement (needs {required_years} year(s)).",
    )


def _evaluation(
    requirement: JobRequirement,
    priority,
    *,
    signal: MatchSignal,
    status: RequirementStatus,
    evidence_experiences: tuple[Experience, ...],
    explanation: str,
) -> RequirementEvaluation:
    strength = strength_for_signal(signal)
    evidence = tuple(
        MatchEvidence(
            evidence=experience.evidence,
            source_type="EXPERIENCE",
            source_label=" at ".join(p for p in (experience.title, experience.company) if p) or None,
        )
        for experience in evidence_experiences
        if experience.evidence is not None
    )
    return RequirementEvaluation(
        requirement_type=requirement.requirement_type,
        priority=priority,
        raw_text=requirement.raw_text,
        status=status,
        match_signal=signal,
        match_strength=strength,
        score=SCORE_FOR_STRENGTH[strength],
        confidence=confidence_for_signal(signal),
        evidence=evidence,
        explanation=explanation,
    )


def _parse_year_range(
    start_raw: str | None, end_raw: str | None, reference_year: int
) -> tuple[int, int] | None:
    start_match = _YEAR_RE.search(start_raw) if start_raw else None
    if not start_match:
        return None
    start_year = int(start_match.group(0))

    if not end_raw or _PRESENT_RE.search(end_raw):
        end_year = reference_year
    else:
        end_match = _YEAR_RE.search(end_raw)
        end_year = int(end_match.group(0)) if end_match else reference_year

    if end_year < start_year:
        return None
    return (start_year, end_year)


def _merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged
