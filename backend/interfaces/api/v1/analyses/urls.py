from django.urls import path

from interfaces.api.v1.analyses.views import AnalysisDetailView, AnalysisListCreateView, AnalysisStatusView

urlpatterns = [
    path("", AnalysisListCreateView.as_view(), name="analysis-list-create"),
    path("<uuid:analysis_id>/", AnalysisDetailView.as_view(), name="analysis-detail"),
    path("<uuid:analysis_id>/status/", AnalysisStatusView.as_view(), name="analysis-status"),
]
