from django.urls import path

from interfaces.api.v1.cvs.views import CvDetailView, CvListCreateView, CvProfileView, CvStatusView

urlpatterns = [
    path("", CvListCreateView.as_view(), name="cv-list-create"),
    path("<uuid:document_id>/", CvDetailView.as_view(), name="cv-detail"),
    path("<uuid:document_id>/status/", CvStatusView.as_view(), name="cv-status"),
    path("<uuid:document_id>/profile/", CvProfileView.as_view(), name="cv-profile"),
]
