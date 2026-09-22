"""API schemas for the CVs resource (section 33: kept separate from
domain models - these read Django model instances but never expose
internal database IDs, storage_reference, or raw extracted text).
"""
from rest_framework import serializers

from apps.candidates.models import (
    CandidateProfile,
    CandidateSkill,
    Certification,
    Education,
    Experience,
    Language,
    Project,
)
from apps.documents.models import Document, Evidence


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


class CandidateSkillSerializer(serializers.ModelSerializer):
    skill = SkillRefSerializer(allow_null=True)
    evidence = EvidenceSerializer(allow_null=True)

    class Meta:
        model = CandidateSkill
        fields = ["raw_text", "skill", "evidence"]


class ExperienceSerializer(serializers.ModelSerializer):
    evidence = EvidenceSerializer(allow_null=True)

    class Meta:
        model = Experience
        fields = [
            "title",
            "company",
            "start_date_raw",
            "end_date_raw",
            "description",
            "achievements",
            "technologies",
            "evidence",
        ]


class EducationSerializer(serializers.ModelSerializer):
    evidence = EvidenceSerializer(allow_null=True)

    class Meta:
        model = Education
        fields = ["institution", "degree", "field_of_study", "start_date_raw", "end_date_raw", "evidence"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name", "description", "technologies"]


class CertificationSerializer(serializers.ModelSerializer):
    evidence = EvidenceSerializer(allow_null=True)

    class Meta:
        model = Certification
        fields = ["name", "issuer", "date_raw", "evidence"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["name", "proficiency"]


class CandidateProfileSerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True)
    education = EducationSerializer(many=True)
    projects = ProjectSerializer(many=True)
    certifications = CertificationSerializer(many=True)
    languages = LanguageSerializer(many=True)
    skills = CandidateSkillSerializer(many=True)

    class Meta:
        model = CandidateProfile
        fields = [
            "full_name",
            "email",
            "phone",
            "location",
            "links",
            "summary",
            "experiences",
            "education",
            "projects",
            "certifications",
            "languages",
            "skills",
        ]
