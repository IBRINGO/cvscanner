from django.contrib import admin

from apps.skills.models import Skill, SkillAlias


class SkillAliasInline(admin.TabularInline):
    model = SkillAlias
    extra = 1


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("canonical_name", "category", "parent")
    list_filter = ("category",)
    search_fields = ("canonical_name",)
    inlines = [SkillAliasInline]
