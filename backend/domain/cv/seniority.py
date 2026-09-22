"""Seniority normalization (Phase 3 section 15).

Maps a raw, human-written title ("Senior Software Engineer", "Tech
Lead") to a small controlled vocabulary. This is keyword matching over
the title text only - it never infers seniority from years of
experience, company size, or anything not literally present in the
title. A title with no recognizable seniority keyword normalizes to
UNKNOWN rather than a guessed default; UNKNOWN is a legitimate result,
not a failure.
"""
import re
from enum import StrEnum


class SeniorityLevel(StrEnum):
    INTERN = "INTERN"
    JUNIOR = "JUNIOR"
    MID = "MID"
    SENIOR = "SENIOR"
    LEAD = "LEAD"
    MANAGER = "MANAGER"
    DIRECTOR = "DIRECTOR"
    EXECUTIVE = "EXECUTIVE"
    UNKNOWN = "UNKNOWN"


# Checked in this order (most specific / most senior first) so a title
# like "Senior Engineering Manager" resolves to MANAGER rather than
# SENIOR - the more specific role keyword wins over a generic modifier.
_SENIORITY_KEYWORDS: tuple[tuple[SeniorityLevel, re.Pattern[str]], ...] = (
    (
        SeniorityLevel.EXECUTIVE,
        re.compile(r"\b(chief|cto|ceo|coo|cfo|vp|vice president)\b", re.IGNORECASE),
    ),
    (SeniorityLevel.DIRECTOR, re.compile(r"\b(director|head of)\b", re.IGNORECASE)),
    (SeniorityLevel.MANAGER, re.compile(r"\b(manager|managing)\b", re.IGNORECASE)),
    (
        SeniorityLevel.LEAD,
        re.compile(r"\b(lead|leads|principal|staff|tech lead|team lead)\b", re.IGNORECASE),
    ),
    (
        SeniorityLevel.SENIOR,
        re.compile(r"\b(senior|sr\.?|confirmed)\b", re.IGNORECASE),
    ),
    (
        SeniorityLevel.INTERN,
        re.compile(r"\b(intern|internship|stagiaire|trainee)\b", re.IGNORECASE),
    ),
    (
        SeniorityLevel.JUNIOR,
        re.compile(r"\b(junior|jr\.?|entry.level|associate)\b", re.IGNORECASE),
    ),
    (SeniorityLevel.MID, re.compile(r"\b(mid.level|intermediate)\b", re.IGNORECASE)),
)


def normalize_seniority(raw_title: str | None) -> SeniorityLevel:
    """Returns the seniority implied by an explicit keyword in
    `raw_title`. Does not fall back to MID for an ordinary, unqualified
    title ("Software Engineer") - that title simply does not state a
    seniority, so the honest result is UNKNOWN, not a guessed default.
    """
    if not raw_title:
        return SeniorityLevel.UNKNOWN

    for level, pattern in _SENIORITY_KEYWORDS:
        if pattern.search(raw_title):
            return level

    return SeniorityLevel.UNKNOWN
