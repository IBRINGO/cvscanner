"""Views for the Skills resource (Phase 3 section 59): browsing the
taxonomy and a single skill's relationships. Read-only - skills are
seeded/managed via migrations and the admin, not this API.
"""
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from domain.skills.relationships import build_relationship_view
from infrastructure.database.repositories.skill_repository import DjangoSkillRepository
from interfaces.api.v1.skills.serializers import SkillDetailSerializer, SkillRefSerializer


class SkillListView(APIView):
    def get(self, request):
        skills = DjangoSkillRepository().all()
        return Response(SkillRefSerializer(skills, many=True).data)


class SkillDetailView(APIView):
    def get(self, request, canonical_name):
        skills = DjangoSkillRepository().all()
        skill = next((s for s in skills if s.canonical_name == canonical_name), None)
        if skill is None:
            raise Http404(f"No skill named {canonical_name!r}")
        view = build_relationship_view(skill, skills)
        return Response(SkillDetailSerializer(view).data)
