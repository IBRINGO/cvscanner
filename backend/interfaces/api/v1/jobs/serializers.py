"""API schemas for the Jobs resource. See interfaces/api/v1/cvs/serializers.py
for the same design principle (no internal IDs, no domain objects
exposed directly).
"""
from rest_framework import serializers

from apps.documents.models import Document, Evidence
from apps.jobs.models import JobProfile, JobRequirement


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ["page_number", "section", "text", "confidence", "extraction_method"]


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "document_type",
            "original_filename",
            "mime_type",
            "file_size",
            "status",
            "page_count",
            "created_at",
            "updated_at",
        ]


class DocumentStatusSerializer(serializers.ModelSerializer):
    error = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "status", "error", "updated_at"]

    def get_error(self, obj: Document) -> str | None:
        return obj.processing_metadata.get("error")


class SkillRefSerializer(serializers.Serializer):
    canonical_name = serializers.CharField()
    category = serializers.CharField()


class JobRequirementSerializer(serializers.ModelSerializer):
    skill = SkillRefSerializer(allow_null=True)
    evidence = EvidenceSerializer(allow_null=True)

    class Meta:
        model = JobRequirement
        fields = ["requirement_type", "importance", "raw_text", "skill", "evidence"]


class JobProfileSerializer(serializers.ModelSerializer):
    requirements = JobRequirementSerializer(many=True)

    class Meta:
        model = JobProfile
        fields = [
            "title",
            "company",
            "location",
            "employment_type",
            "seniority",
            "summary",
            "responsibilities",
            "requirements",
        ]
