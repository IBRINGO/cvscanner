from django.contrib import admin

from apps.jobs.models import JobProfile, JobRequirement


class JobRequirementInline(admin.TabularInline):
    model = JobRequirement
    extra = 0


@admin.register(JobProfile)
class JobProfileAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "document")
    search_fields = ("title", "company")
    inlines = [JobRequirementInline]
