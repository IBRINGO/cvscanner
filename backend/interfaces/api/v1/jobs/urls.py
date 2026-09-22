from django.urls import path

from interfaces.api.v1.jobs.views import (
    JobDetailView,
    JobListCreateView,
    JobProfileDetailView,
    JobStatusView,
)

urlpatterns = [
    path("", JobListCreateView.as_view(), name="job-list-create"),
    path("<uuid:document_id>/", JobDetailView.as_view(), name="job-detail"),
    path("<uuid:document_id>/status/", JobStatusView.as_view(), name="job-status"),
    path("<uuid:document_id>/profile/", JobProfileDetailView.as_view(), name="job-profile"),
]
