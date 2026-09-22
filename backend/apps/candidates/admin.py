from django.contrib import admin

from apps.candidates.models import (
    CandidateProfile,
    CandidateSkill,
    Certification,
    Education,
    Experience,
    Language,
    Project,
)


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class CandidateSkillInline(admin.TabularInline):
    model = CandidateSkill
    extra = 0


@admin.register(CandidateProfile)
class CandidateProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "document")
    search_fields = ("full_name", "email")
    inlines = [ExperienceInline, EducationInline, CandidateSkillInline]


admin.site.register(Project)
admin.site.register(Certification)
admin.site.register(Language)
