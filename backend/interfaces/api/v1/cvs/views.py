"""Views for the CVs resource (sections 8, 25, 31-33 of the Phase 2
brief). Thin by design: parse the request, call an application use case
via config/container.py, serialize the result. No business logic lives
here - see docs/architecture/dependency-rule.md.
"""
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.candidates.models import CandidateProfile
from apps.documents.models import Document
from config.container import build_upload_document
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.documents.exceptions import DocumentValidationError
from interfaces.api.v1.cvs.pdf_rendering import render_cv_pdf
from interfaces.api.v1.cvs.serializers import (
    CandidateProfileSerializer,
    DocumentSerializer,
    DocumentStatusSerializer,
)
from workers.tasks.document_tasks import process_cv_document


class CvListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        documents = Document.objects.filter(document_type=DocumentType.CV.value)
        return Response(DocumentSerializer(documents, many=True).data)

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        if uploaded_file is None:
            return Response({"detail": "No file was submitted."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = build_upload_document().execute(
                document_type=DocumentType.CV,
                content=uploaded_file.read(),
                original_filename=uploaded_file.name,
                mime_type=uploaded_file.content_type or "application/octet-stream",
            )
        except DocumentValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if result.needs_processing:
            process_cv_document.delay(result.document.id)

        document_row = Document.objects.get(id=result.document.id)
        return Response(DocumentSerializer(document_row).data, status=status.HTTP_202_ACCEPTED)


class CvDetailView(APIView):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, document_type=DocumentType.CV.value)
        return Response(DocumentSerializer(document).data)


class CvStatusView(APIView):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, document_type=DocumentType.CV.value)
        return Response(DocumentStatusSerializer(document).data)


class CvProfileView(APIView):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, document_type=DocumentType.CV.value)

        profile = None
        if document.status == ProcessingStatus.PROCESSED.value:
            candidate_profile = CandidateProfile.objects.filter(document=document).first()
            if candidate_profile is not None:
                profile = CandidateProfileSerializer(candidate_profile).data

        return Response({"document_id": str(document.id), "status": document.status, "profile": profile})


class CvRenderPdfView(APIView):
    """Stateless PDF rendering for the editor's "Download PDF" action -
    see interfaces/api/v1/cvs/pdf_rendering.py for why this is the one
    editor-facing endpoint (it renders, it never validates or persists
    the submitted profile as a candidate fact)."""

    def post(self, request):
        profile = request.data.get("profile")
        if not isinstance(profile, dict):
            return Response({"detail": "A 'profile' object is required."}, status=status.HTTP_400_BAD_REQUEST)

        template_id = request.data.get("template_id") or "ats-classic"
        section_order = request.data.get("section_order") or []
        hidden_section_ids = request.data.get("hidden_section_ids") or []

        pdf_bytes = render_cv_pdf(profile, template_id, section_order, hidden_section_ids)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = (profile.get("full_name") or "cv").strip().replace(" ", "-").lower() or "cv"
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response
