from django.contrib import admin

from apps.skills.models import Skill, SkillAlias, SkillRelation


class SkillAliasInline(admin.TabularInline):
    model = SkillAlias
    extra = 1


class SkillRelationInline(admin.TabularInline):
    model = SkillRelation
    fk_name = "from_skill"
    extra = 1


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("canonical_name", "category", "parent", "ecosystem")
    list_filter = ("category", "ecosystem")
    search_fields = ("canonical_name",)
    inlines = [SkillAliasInline, SkillRelationInline]
