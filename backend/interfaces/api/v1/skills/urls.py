from django.urls import path

from interfaces.api.v1.skills.views import SkillDetailView, SkillListView

urlpatterns = [
    path("", SkillListView.as_view(), name="skill-list"),
    path("<str:canonical_name>/", SkillDetailView.as_view(), name="skill-detail"),
]
