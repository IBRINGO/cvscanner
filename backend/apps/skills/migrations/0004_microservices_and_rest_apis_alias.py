"""Adds the "Microservices" skill (entirely missing from the seed
taxonomy - see domain/skills/taxonomy.py) and a "rest apis" alias for
the existing "REST" skill.

Found via a real analysis run: a candidate CV listing "REST APIs" and
"Microservices" verbatim under Skills failed to match a job posting
requiring the exact same terms. Root cause: REST's alias list only
covered the singular "rest api" (normalize_skill_name does exact
matching, no plural stripping) and "Microservices" had no taxonomy
entry at all, so neither term could ever resolve regardless of
phrasing. Hardcodes the exact literal strings (rather than importing
SEED_SKILLS) so this migration's effect stays fixed even if the seed
taxonomy is edited again later.
"""
from django.db import migrations


def add_entries(apps, schema_editor):
    Skill = apps.get_model("skills", "Skill")
    SkillAlias = apps.get_model("skills", "SkillAlias")

    rest = Skill.objects.filter(canonical_name="REST").first()
    if rest is not None:
        for alias in ("rest apis", "restful api", "restful apis"):
            SkillAlias.objects.get_or_create(skill=rest, alias=alias)

    microservices, _ = Skill.objects.get_or_create(
        canonical_name="Microservices", defaults={"category": "METHODOLOGY"}
    )
    for alias in ("microservice", "microservices architecture"):
        SkillAlias.objects.get_or_create(skill=microservices, alias=alias)


def remove_entries(apps, schema_editor):
    Skill = apps.get_model("skills", "Skill")
    SkillAlias = apps.get_model("skills", "SkillAlias")

    rest = Skill.objects.filter(canonical_name="REST").first()
    if rest is not None:
        SkillAlias.objects.filter(
            skill=rest, alias__in=("rest apis", "restful api", "restful apis")
        ).delete()

    Skill.objects.filter(canonical_name="Microservices").delete()


class Migration(migrations.Migration):
    dependencies = [("skills", "0003_skill_relationships")]

    operations = [migrations.RunPython(add_entries, remove_entries)]
