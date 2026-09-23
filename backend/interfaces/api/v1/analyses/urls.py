from django.urls import path

from interfaces.api.v1.analyses.views import AnalysisDetailView, AnalysisListCreateView, AnalysisStatusView
from interfaces.api.v1.recommendations.views import AnalysisRecommendationsView

urlpatterns = [
    path("", AnalysisListCreateView.as_view(), name="analysis-list-create"),
    path("<uuid:analysis_id>/", AnalysisDetailView.as_view(), name="analysis-detail"),
    path("<uuid:analysis_id>/status/", AnalysisStatusView.as_view(), name="analysis-status"),
    path(
        "<uuid:analysis_id>/recommendations/",
        AnalysisRecommendationsView.as_view(),
        name="analysis-recommendations",
    ),
]
