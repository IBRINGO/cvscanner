from enum import StrEnum


class SemanticEntityType(StrEnum):
    """What a SemanticRepresentation's embedding was computed for. Kept
    separate from domain/documents/enums.py::SectionType - a semantic
    entity is a *fact* (an experience, a requirement, a skill...), not a
    document section.
    """

    CANDIDATE_PROFILE = "CANDIDATE_PROFILE"
    JOB_PROFILE = "JOB_PROFILE"
    EXPERIENCE = "EXPERIENCE"
    JOB_REQUIREMENT = "JOB_REQUIREMENT"
    SKILL = "SKILL"
