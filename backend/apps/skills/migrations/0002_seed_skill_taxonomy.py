"""Seeds the initial skill taxonomy from domain/skills/taxonomy.py.

Reversible: the reverse migration deletes every Skill/SkillAlias, so this
migration can be safely reversed and re-applied without leftover rows.
Runs in two passes (create skills, then wire parent/related links) since
`parent`/`related_skills` reference other Skill rows that must exist
first.
"""
from django.db import migrations

from domain.skills.taxonomy import SEED_SKILLS


def seed_taxonomy(apps, schema_editor):
    Skill = apps.get_model("skills", "Skill")
    SkillAlias = apps.get_model("skills", "SkillAlias")

    created = {}
    for entry in SEED_SKILLS:
        skill = Skill.objects.create(canonical_name=entry.canonical_name, category=entry.category.value)
        created[entry.canonical_name] = skill
        for alias in entry.aliases:
            SkillAlias.objects.create(skill=skill, alias=alias)

    for entry in SEED_SKILLS:
        if not entry.parent_skill:
            continue
        skill = created[entry.canonical_name]
        skill.parent = created.get(entry.parent_skill)
        skill.save(update_fields=["parent"])

    for entry in SEED_SKILLS:
        for related_name in entry.related_skills:
            related = created.get(related_name)
            if related:
                created[entry.canonical_name].related_skills.add(related)


def unseed_taxonomy(apps, schema_editor):
    Skill = apps.get_model("skills", "Skill")
    Skill.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("skills", "0001_initial")]

    operations = [migrations.RunPython(seed_taxonomy, unseed_taxonomy)]
