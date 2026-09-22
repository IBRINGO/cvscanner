"""Seed skill taxonomy.

This is a clean starting dataset, not an attempt at an exhaustive skills
knowledge base - see section 18 of the Phase 2 brief (and section 10 of
the Phase 3 brief: quality over quantity). It exists so normalization has
something real to match against, and so the data migration in
apps/skills/migrations has a single source of truth to seed from (domain
code, not a raw SQL fixture, so the same list drives both the DB seed and
framework-free unit tests).

Phase 3 additions: `description` (a one-line, factual gloss - never a
proficiency claim), `ecosystem` (skills commonly used together, not
equivalent - see domain/skills/entities.py), and `relations` (a small,
deliberately curated set of RELATED_TO / ALTERNATIVE_TO / BUILDS_ON
edges). Not every skill needs an ecosystem or a relation; most don't, and
that is fine. PARENT_OF / CHILD_OF / PART_OF_ECOSYSTEM are never stored
here - they are derived from `parent_skill` / `ecosystem` at read time
(domain/skills/relationships.py).

Grow this list by adding entries here and running a new data migration -
see apps/skills/migrations/0002_seed_skill_taxonomy.py and
apps/skills/migrations/0003_skill_relationships.py.
"""
from domain.skills.entities import Skill, SkillRelation
from domain.skills.enums import SkillCategory, SkillRelationType

_ALT = SkillRelationType.ALTERNATIVE_TO
_REL = SkillRelationType.RELATED_TO
_BUILDS = SkillRelationType.BUILDS_ON

_PYTHON_ECOSYSTEM = "Python ecosystem"
_JS_ECOSYSTEM = "JavaScript ecosystem"
_JVM_ECOSYSTEM = "Java ecosystem"
_DOTNET_ECOSYSTEM = ".NET ecosystem"
_PHP_ECOSYSTEM = "PHP ecosystem"
_RUBY_ECOSYSTEM = "Ruby ecosystem"

SEED_SKILLS: tuple[Skill, ...] = (
    # Programming languages
    Skill(
        "Python",
        SkillCategory.PROGRAMMING_LANGUAGE,
        aliases=("py",),
        ecosystem=_PYTHON_ECOSYSTEM,
        description="A general-purpose, dynamically typed programming language.",
    ),
    Skill(
        "Java",
        SkillCategory.PROGRAMMING_LANGUAGE,
        ecosystem=_JVM_ECOSYSTEM,
        description="A statically typed, object-oriented language that runs on the JVM.",
    ),
    Skill(
        "JavaScript",
        SkillCategory.PROGRAMMING_LANGUAGE,
        aliases=("js", "javascript", "ecmascript"),
        ecosystem=_JS_ECOSYSTEM,
        description="The scripting language of the web, standardized as ECMAScript.",
    ),
    Skill(
        "TypeScript",
        SkillCategory.PROGRAMMING_LANGUAGE,
        aliases=("ts",),
        ecosystem=_JS_ECOSYSTEM,
        description="A statically typed superset of JavaScript that compiles to it.",
        relations=(SkillRelation("JavaScript", _BUILDS),),
    ),
    Skill(
        "C#",
        SkillCategory.PROGRAMMING_LANGUAGE,
        aliases=("csharp", "c sharp"),
        ecosystem=_DOTNET_ECOSYSTEM,
        description="A statically typed language built for the .NET platform.",
    ),
    Skill(
        "C++",
        SkillCategory.PROGRAMMING_LANGUAGE,
        aliases=("cpp",),
        description="A compiled, statically typed systems programming language.",
    ),
    Skill(
        "Go",
        SkillCategory.PROGRAMMING_LANGUAGE,
        aliases=("golang",),
        description="A compiled language designed for simplicity and concurrency.",
    ),
    Skill(
        "Rust",
        SkillCategory.PROGRAMMING_LANGUAGE,
        description="A compiled systems language focused on memory safety without a garbage collector.",
    ),
    Skill(
        "PHP",
        SkillCategory.PROGRAMMING_LANGUAGE,
        ecosystem=_PHP_ECOSYSTEM,
        description="A server-side scripting language widely used for web development.",
    ),
    Skill(
        "Ruby",
        SkillCategory.PROGRAMMING_LANGUAGE,
        ecosystem=_RUBY_ECOSYSTEM,
        description="A dynamically typed, object-oriented scripting language.",
    ),
    Skill(
        "SQL",
        SkillCategory.PROGRAMMING_LANGUAGE,
        description="A declarative language for querying and managing relational data.",
        relations=(SkillRelation("PostgreSQL", _REL), SkillRelation("MySQL", _REL)),
    ),
    # Web frameworks / libraries
    Skill(
        "React",
        SkillCategory.FRAMEWORK,
        aliases=("react.js", "reactjs"),
        parent_skill="JavaScript",
        ecosystem=_JS_ECOSYSTEM,
        description="A component-based library for building user interfaces.",
        relations=(SkillRelation("Vue.js", _ALT), SkillRelation("Angular", _ALT)),
    ),
    Skill(
        "Angular",
        SkillCategory.FRAMEWORK,
        parent_skill="TypeScript",
        ecosystem=_JS_ECOSYSTEM,
        description="A full-featured, opinionated frontend framework built with TypeScript.",
        relations=(SkillRelation("React", _ALT), SkillRelation("Vue.js", _ALT)),
    ),
    Skill(
        "Vue.js",
        SkillCategory.FRAMEWORK,
        aliases=("vue", "vuejs"),
        parent_skill="JavaScript",
        ecosystem=_JS_ECOSYSTEM,
        description="An approachable, incrementally adoptable frontend framework.",
        relations=(SkillRelation("React", _ALT), SkillRelation("Angular", _ALT)),
    ),
    Skill(
        "Next.js",
        SkillCategory.FRAMEWORK,
        aliases=("nextjs",),
        parent_skill="React",
        ecosystem=_JS_ECOSYSTEM,
        description="A React framework adding server rendering and file-based routing.",
        relations=(SkillRelation("React", _BUILDS),),
    ),
    Skill(
        "Node.js",
        SkillCategory.FRAMEWORK,
        aliases=("nodejs", "node"),
        parent_skill="JavaScript",
        ecosystem=_JS_ECOSYSTEM,
        description="A JavaScript runtime for building server-side applications.",
    ),
    Skill(
        "Express",
        SkillCategory.FRAMEWORK,
        aliases=("express.js", "expressjs"),
        parent_skill="Node.js",
        ecosystem=_JS_ECOSYSTEM,
        description="A minimal web application framework for Node.js.",
        relations=(SkillRelation("Node.js", _BUILDS),),
    ),
    Skill(
        "Django",
        SkillCategory.FRAMEWORK,
        parent_skill="Python",
        ecosystem=_PYTHON_ECOSYSTEM,
        description="A batteries-included web framework for Python.",
        relations=(SkillRelation("Flask", _ALT), SkillRelation("FastAPI", _ALT)),
    ),
    Skill(
        "Django REST Framework",
        SkillCategory.FRAMEWORK,
        aliases=("drf",),
        parent_skill="Django",
        ecosystem=_PYTHON_ECOSYSTEM,
        description="A toolkit for building REST APIs on top of Django.",
        relations=(SkillRelation("Django", _BUILDS),),
    ),
    Skill(
        "Flask",
        SkillCategory.FRAMEWORK,
        parent_skill="Python",
        ecosystem=_PYTHON_ECOSYSTEM,
        description="A lightweight, unopinionated web framework for Python.",
        relations=(SkillRelation("Django", _ALT), SkillRelation("FastAPI", _ALT)),
    ),
    Skill(
        "FastAPI",
        SkillCategory.FRAMEWORK,
        parent_skill="Python",
        ecosystem=_PYTHON_ECOSYSTEM,
        description="A high-performance Python web framework built on type hints.",
        relations=(SkillRelation("Django", _ALT), SkillRelation("Flask", _ALT)),
    ),
    Skill(
        "Spring Boot",
        SkillCategory.FRAMEWORK,
        aliases=("spring",),
        parent_skill="Java",
        ecosystem=_JVM_ECOSYSTEM,
        description="An opinionated framework for building Java applications and services.",
    ),
    Skill(
        ".NET",
        SkillCategory.FRAMEWORK,
        aliases=("dotnet", "dot net"),
        parent_skill="C#",
        ecosystem=_DOTNET_ECOSYSTEM,
        description="A cross-platform framework for building applications with C#.",
    ),
    Skill(
        "Laravel",
        SkillCategory.FRAMEWORK,
        parent_skill="PHP",
        ecosystem=_PHP_ECOSYSTEM,
        description="A web application framework with expressive, elegant syntax for PHP.",
    ),
    Skill(
        "Ruby on Rails",
        SkillCategory.FRAMEWORK,
        aliases=("rails",),
        parent_skill="Ruby",
        ecosystem=_RUBY_ECOSYSTEM,
        description="A convention-over-configuration web framework for Ruby.",
    ),
    # Databases
    Skill(
        "PostgreSQL",
        SkillCategory.DATABASE,
        aliases=("postgres",),
        description="An open-source, extensible relational database system.",
        relations=(SkillRelation("MySQL", _ALT), SkillRelation("MongoDB", _ALT)),
    ),
    Skill(
        "MySQL",
        SkillCategory.DATABASE,
        description="A widely used open-source relational database system.",
        relations=(SkillRelation("PostgreSQL", _ALT),),
    ),
    Skill(
        "SQLite",
        SkillCategory.DATABASE,
        description="A lightweight, file-based relational database engine.",
    ),
    Skill(
        "MongoDB",
        SkillCategory.DATABASE,
        aliases=("mongo",),
        description="A document-oriented NoSQL database.",
        relations=(SkillRelation("PostgreSQL", _ALT),),
    ),
    Skill(
        "Redis",
        SkillCategory.DATABASE,
        description="An in-memory key-value store used for caching and messaging.",
    ),
    Skill(
        "Elasticsearch",
        SkillCategory.DATABASE,
        description="A distributed search and analytics engine.",
    ),
    # Cloud
    Skill(
        "Amazon Web Services",
        SkillCategory.CLOUD,
        aliases=("aws",),
        description="A cloud computing platform offering on-demand infrastructure services.",
        relations=(
            SkillRelation("Google Cloud Platform", _ALT),
            SkillRelation("Microsoft Azure", _ALT),
        ),
    ),
    Skill(
        "Google Cloud Platform",
        SkillCategory.CLOUD,
        aliases=("gcp", "google cloud"),
        description="Google's cloud computing platform for infrastructure and managed services.",
        relations=(SkillRelation("Amazon Web Services", _ALT), SkillRelation("Microsoft Azure", _ALT)),
    ),
    Skill(
        "Microsoft Azure",
        SkillCategory.CLOUD,
        aliases=("azure",),
        description="Microsoft's cloud computing platform for infrastructure and managed services.",
        relations=(
            SkillRelation("Amazon Web Services", _ALT),
            SkillRelation("Google Cloud Platform", _ALT),
        ),
    ),
    # DevOps / tools
    Skill(
        "Docker",
        SkillCategory.DEVOPS,
        description="A platform for packaging and running applications in containers.",
    ),
    Skill(
        "Kubernetes",
        SkillCategory.DEVOPS,
        aliases=("k8s",),
        description="A container orchestration platform for deploying and scaling applications.",
        relations=(SkillRelation("Docker", _BUILDS),),
    ),
    Skill(
        "Terraform",
        SkillCategory.DEVOPS,
        description="A tool for defining cloud infrastructure as code.",
    ),
    Skill(
        "Jenkins",
        SkillCategory.DEVOPS,
        description="An automation server commonly used to run CI/CD pipelines.",
        relations=(SkillRelation("CI/CD", _REL),),
    ),
    Skill("Git", SkillCategory.TOOL, description="A distributed version control system."),
    Skill(
        "GitHub Actions",
        SkillCategory.DEVOPS,
        description="A CI/CD automation platform built into GitHub.",
        relations=(SkillRelation("CI/CD", _REL),),
    ),
    Skill(
        "CI/CD",
        SkillCategory.METHODOLOGY,
        aliases=("ci cd", "continuous integration"),
        description="The practice of automating build, test, and deployment pipelines.",
    ),
    # Data / AI
    Skill(
        "Pandas",
        SkillCategory.DATA,
        parent_skill="Python",
        ecosystem=_PYTHON_ECOSYSTEM,
        description="A data manipulation and analysis library for Python.",
    ),
    Skill(
        "NumPy",
        SkillCategory.DATA,
        parent_skill="Python",
        ecosystem=_PYTHON_ECOSYSTEM,
        description="A library for numerical computing with array data in Python.",
    ),
    Skill(
        "Machine Learning",
        SkillCategory.AI_ML,
        aliases=("ml",),
        description="Building systems that learn patterns from data rather than fixed rules.",
    ),
    Skill(
        "Deep Learning",
        SkillCategory.AI_ML,
        parent_skill="Machine Learning",
        description="Machine learning using multi-layer neural networks.",
    ),
    Skill(
        "TensorFlow",
        SkillCategory.AI_ML,
        ecosystem=_PYTHON_ECOSYSTEM,
        description="An open-source framework for building and training machine learning models.",
        relations=(SkillRelation("PyTorch", _ALT),),
    ),
    Skill(
        "PyTorch",
        SkillCategory.AI_ML,
        ecosystem=_PYTHON_ECOSYSTEM,
        description="An open-source machine learning framework favored for research.",
        relations=(SkillRelation("TensorFlow", _ALT),),
    ),
    # Web
    Skill("HTML", SkillCategory.WEB, aliases=("html5",), description="The markup language of the web."),
    Skill("CSS", SkillCategory.WEB, aliases=("css3",), description="The styling language of the web."),
    Skill(
        "Sass",
        SkillCategory.WEB,
        aliases=("scss",),
        parent_skill="CSS",
        description="A CSS preprocessor adding variables, nesting, and mixins.",
    ),
    Skill(
        "Tailwind CSS",
        SkillCategory.WEB,
        aliases=("tailwind",),
        parent_skill="CSS",
        description="A utility-first CSS framework.",
    ),
    Skill(
        "REST",
        SkillCategory.WEB,
        aliases=("rest api", "restful"),
        description="An architectural style for stateless HTTP APIs.",
        relations=(SkillRelation("GraphQL", _ALT),),
    ),
    Skill(
        "GraphQL",
        SkillCategory.WEB,
        description="A query language and runtime for APIs that lets clients shape responses.",
        relations=(SkillRelation("REST", _ALT),),
    ),
    # Mobile
    Skill("Swift", SkillCategory.MOBILE, description="Apple's language for iOS and macOS development."),
    Skill(
        "Kotlin",
        SkillCategory.MOBILE,
        description="A statically typed language used for Android development.",
    ),
    Skill(
        "Flutter",
        SkillCategory.MOBILE,
        description="A cross-platform UI toolkit for building mobile apps from one codebase.",
        relations=(SkillRelation("React Native", _ALT),),
    ),
    Skill(
        "React Native",
        SkillCategory.MOBILE,
        parent_skill="React",
        description="A framework for building native mobile apps using React.",
        relations=(SkillRelation("Flutter", _ALT),),
    ),
    # Testing
    Skill(
        "Jest",
        SkillCategory.TESTING,
        ecosystem=_JS_ECOSYSTEM,
        description="A JavaScript testing framework.",
    ),
    Skill(
        "Pytest",
        SkillCategory.TESTING,
        parent_skill="Python",
        ecosystem=_PYTHON_ECOSYSTEM,
        description="A testing framework for Python.",
    ),
    Skill(
        "Selenium",
        SkillCategory.TESTING,
        description="A browser automation tool used for end-to-end testing.",
    ),
    # Methodology
    Skill("Agile", SkillCategory.METHODOLOGY, description="An iterative approach to software delivery."),
    Skill(
        "Scrum",
        SkillCategory.METHODOLOGY,
        parent_skill="Agile",
        description="A framework for applying Agile through fixed-length sprints.",
    ),
    # Software / tools
    Skill(
        "Linux",
        SkillCategory.SOFTWARE,
        description="A family of open-source Unix-like operating systems.",
    ),
    Skill("Jira", SkillCategory.TOOL, description="A project and issue tracking tool."),
    Skill("Figma", SkillCategory.TOOL, description="A collaborative interface design tool."),
)
