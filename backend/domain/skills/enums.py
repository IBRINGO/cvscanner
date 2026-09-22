from enum import StrEnum


class SkillCategory(StrEnum):
    """Initial Phase 2 taxonomy (see domain/skills/taxonomy.py for the
    seed dataset). Documented as extensible: adding a category here and a
    handful of Skill entries is expected to happen often; this is not a
    closed list.
    """

    PROGRAMMING_LANGUAGE = "PROGRAMMING_LANGUAGE"
    FRAMEWORK = "FRAMEWORK"
    LIBRARY = "LIBRARY"
    DATABASE = "DATABASE"
    CLOUD = "CLOUD"
    DEVOPS = "DEVOPS"
    DATA = "DATA"
    AI_ML = "AI_ML"
    WEB = "WEB"
    MOBILE = "MOBILE"
    TESTING = "TESTING"
    SOFTWARE = "SOFTWARE"
    METHODOLOGY = "METHODOLOGY"
    TOOL = "TOOL"
