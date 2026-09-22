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


class SkillDomain(StrEnum):
    """A coarser grouping over SkillCategory, used for frontend clustering
    (Phase 3 section 10). Additive: every SkillCategory maps to exactly
    one SkillDomain via `skill_domain_for_category` below, so this can be
    introduced without touching the existing category values or any
    stored data.
    """

    SOFTWARE_DEVELOPMENT = "SOFTWARE_DEVELOPMENT"
    DATA_AND_AI = "DATA_AND_AI"
    CLOUD_AND_INFRASTRUCTURE = "CLOUD_AND_INFRASTRUCTURE"
    ENGINEERING_PRACTICES = "ENGINEERING_PRACTICES"


_CATEGORY_TO_DOMAIN: dict[SkillCategory, SkillDomain] = {
    SkillCategory.PROGRAMMING_LANGUAGE: SkillDomain.SOFTWARE_DEVELOPMENT,
    SkillCategory.FRAMEWORK: SkillDomain.SOFTWARE_DEVELOPMENT,
    SkillCategory.LIBRARY: SkillDomain.SOFTWARE_DEVELOPMENT,
    SkillCategory.WEB: SkillDomain.SOFTWARE_DEVELOPMENT,
    SkillCategory.MOBILE: SkillDomain.SOFTWARE_DEVELOPMENT,
    SkillCategory.DATABASE: SkillDomain.DATA_AND_AI,
    SkillCategory.DATA: SkillDomain.DATA_AND_AI,
    SkillCategory.AI_ML: SkillDomain.DATA_AND_AI,
    SkillCategory.CLOUD: SkillDomain.CLOUD_AND_INFRASTRUCTURE,
    SkillCategory.DEVOPS: SkillDomain.CLOUD_AND_INFRASTRUCTURE,
    SkillCategory.TESTING: SkillDomain.ENGINEERING_PRACTICES,
    SkillCategory.SOFTWARE: SkillDomain.ENGINEERING_PRACTICES,
    SkillCategory.METHODOLOGY: SkillDomain.ENGINEERING_PRACTICES,
    SkillCategory.TOOL: SkillDomain.ENGINEERING_PRACTICES,
}


def skill_domain_for_category(category: SkillCategory) -> SkillDomain:
    return _CATEGORY_TO_DOMAIN[category]


class SkillRelationType(StrEnum):
    """Explicit, typed relationships between two distinct skills (Phase 3
    section 9). Never used to imply equivalence - see
    domain/skills/relationships.py's module docstring.

    PARENT_OF / CHILD_OF and PART_OF_ECOSYSTEM are derived automatically
    from `Skill.parent_skill` / `Skill.ecosystem` (section 8: "do not make
    all relationships bidirectional manually if the data model can derive
    them") and never appear inside `Skill.relations`. Only the remaining,
    genuinely editorial relationships are stored explicitly.
    """

    PARENT_OF = "PARENT_OF"
    CHILD_OF = "CHILD_OF"
    PART_OF_ECOSYSTEM = "PART_OF_ECOSYSTEM"
    RELATED_TO = "RELATED_TO"
    ALTERNATIVE_TO = "ALTERNATIVE_TO"
    BUILDS_ON = "BUILDS_ON"
