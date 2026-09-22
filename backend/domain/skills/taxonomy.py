"""Seed skill taxonomy.

This is a clean starting dataset, not an attempt at an exhaustive skills
knowledge base - see section 18 of the Phase 2 brief. It exists so
normalization has something real to match against, and so the data
migration in apps/skills/migrations has a single source of truth to seed
from (domain code, not a raw SQL fixture, so the same list drives both the
DB seed and framework-free unit tests).

Grow this list by adding entries here and running a new data migration -
see apps/skills/migrations/0002_seed_skill_taxonomy.py.
"""
from domain.skills.entities import Skill
from domain.skills.enums import SkillCategory

SEED_SKILLS: tuple[Skill, ...] = (
    # Programming languages
    Skill("Python", SkillCategory.PROGRAMMING_LANGUAGE, aliases=("py",)),
    Skill("Java", SkillCategory.PROGRAMMING_LANGUAGE),
    Skill(
        "JavaScript",
        SkillCategory.PROGRAMMING_LANGUAGE,
        aliases=("js", "javascript", "ecmascript"),
    ),
    Skill("TypeScript", SkillCategory.PROGRAMMING_LANGUAGE, aliases=("ts",)),
    Skill("C#", SkillCategory.PROGRAMMING_LANGUAGE, aliases=("csharp", "c sharp")),
    Skill("C++", SkillCategory.PROGRAMMING_LANGUAGE, aliases=("cpp",)),
    Skill("Go", SkillCategory.PROGRAMMING_LANGUAGE, aliases=("golang",)),
    Skill("Rust", SkillCategory.PROGRAMMING_LANGUAGE),
    Skill("PHP", SkillCategory.PROGRAMMING_LANGUAGE),
    Skill("Ruby", SkillCategory.PROGRAMMING_LANGUAGE),
    Skill("SQL", SkillCategory.PROGRAMMING_LANGUAGE),
    # Web frameworks / libraries
    Skill(
        "React",
        SkillCategory.FRAMEWORK,
        aliases=("react.js", "reactjs"),
        parent_skill="JavaScript",
    ),
    Skill("Angular", SkillCategory.FRAMEWORK, parent_skill="TypeScript"),
    Skill("Vue.js", SkillCategory.FRAMEWORK, aliases=("vue", "vuejs"), parent_skill="JavaScript"),
    Skill("Next.js", SkillCategory.FRAMEWORK, aliases=("nextjs",), parent_skill="React"),
    Skill("Node.js", SkillCategory.FRAMEWORK, aliases=("nodejs", "node"), parent_skill="JavaScript"),
    Skill("Express", SkillCategory.FRAMEWORK, aliases=("express.js", "expressjs")),
    Skill("Django", SkillCategory.FRAMEWORK, parent_skill="Python"),
    Skill(
        "Django REST Framework",
        SkillCategory.FRAMEWORK,
        aliases=("drf",),
        parent_skill="Django",
    ),
    Skill("Flask", SkillCategory.FRAMEWORK, parent_skill="Python"),
    Skill("FastAPI", SkillCategory.FRAMEWORK, parent_skill="Python"),
    Skill("Spring Boot", SkillCategory.FRAMEWORK, aliases=("spring",), parent_skill="Java"),
    Skill(".NET", SkillCategory.FRAMEWORK, aliases=("dotnet", "dot net"), parent_skill="C#"),
    Skill("Laravel", SkillCategory.FRAMEWORK, parent_skill="PHP"),
    Skill("Ruby on Rails", SkillCategory.FRAMEWORK, aliases=("rails",), parent_skill="Ruby"),
    # Databases
    Skill("PostgreSQL", SkillCategory.DATABASE, aliases=("postgres",)),
    Skill("MySQL", SkillCategory.DATABASE),
    Skill("SQLite", SkillCategory.DATABASE),
    Skill("MongoDB", SkillCategory.DATABASE, aliases=("mongo",)),
    Skill("Redis", SkillCategory.DATABASE),
    Skill("Elasticsearch", SkillCategory.DATABASE),
    # Cloud
    Skill("Amazon Web Services", SkillCategory.CLOUD, aliases=("aws",)),
    Skill("Google Cloud Platform", SkillCategory.CLOUD, aliases=("gcp", "google cloud")),
    Skill("Microsoft Azure", SkillCategory.CLOUD, aliases=("azure",)),
    # DevOps / tools
    Skill("Docker", SkillCategory.DEVOPS),
    Skill("Kubernetes", SkillCategory.DEVOPS, aliases=("k8s",)),
    Skill("Terraform", SkillCategory.DEVOPS),
    Skill("Jenkins", SkillCategory.DEVOPS),
    Skill("Git", SkillCategory.TOOL),
    Skill("GitHub Actions", SkillCategory.DEVOPS),
    Skill("CI/CD", SkillCategory.METHODOLOGY, aliases=("ci cd", "continuous integration")),
    # Data / AI
    Skill("Pandas", SkillCategory.DATA, parent_skill="Python"),
    Skill("NumPy", SkillCategory.DATA, parent_skill="Python"),
    Skill("Machine Learning", SkillCategory.AI_ML, aliases=("ml",)),
    Skill("Deep Learning", SkillCategory.AI_ML),
    Skill("TensorFlow", SkillCategory.AI_ML),
    Skill("PyTorch", SkillCategory.AI_ML),
    # Web
    Skill("HTML", SkillCategory.WEB, aliases=("html5",)),
    Skill("CSS", SkillCategory.WEB, aliases=("css3",)),
    Skill("Sass", SkillCategory.WEB, aliases=("scss",)),
    Skill("Tailwind CSS", SkillCategory.WEB, aliases=("tailwind",)),
    Skill("REST", SkillCategory.WEB, aliases=("rest api", "restful")),
    Skill("GraphQL", SkillCategory.WEB),
    # Mobile
    Skill("Swift", SkillCategory.MOBILE),
    Skill("Kotlin", SkillCategory.MOBILE),
    Skill("Flutter", SkillCategory.MOBILE),
    Skill("React Native", SkillCategory.MOBILE, parent_skill="React"),
    # Testing
    Skill("Jest", SkillCategory.TESTING),
    Skill("Pytest", SkillCategory.TESTING, parent_skill="Python"),
    Skill("Selenium", SkillCategory.TESTING),
    # Methodology
    Skill("Agile", SkillCategory.METHODOLOGY),
    Skill("Scrum", SkillCategory.METHODOLOGY),
    # Software / tools
    Skill("Linux", SkillCategory.SOFTWARE),
    Skill("Jira", SkillCategory.TOOL),
    Skill("Figma", SkillCategory.TOOL),
)
