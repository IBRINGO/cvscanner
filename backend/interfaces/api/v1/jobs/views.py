"""Views for the Jobs resource. Mirrors interfaces/api/v1/cvs/views.py,
with one addition: job offers may be submitted as pasted plain text
(`text` field) instead of a file - see
infrastructure/document_processing/parsers/plain_text_parser.py.
"""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from application.jobs.process_pipeline import PASTED_TEXT_PLACEHOLDER_FILENAME
from apps.documents.models import Document
from apps.jobs.models import JobProfile
from config.container import build_delete_document, build_upload_document
from domain.documents.enums import DocumentType, ProcessingStatus
from domain.documents.exceptions import DocumentValidationError
from interfaces.api.v1.jobs.serializers import (
    DocumentSerializer,
    DocumentStatusSerializer,
    JobProfileSerializer,
)
from workers.tasks.document_tasks import process_job_document


class JobListCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        documents = Document.objects.filter(document_type=DocumentType.JOB_OFFER.value)
        return Response(DocumentSerializer(documents, many=True).data)

    def post(self, request):
        content, filename, mime_type = self._extract_upload(request)
        if content is None:
            return Response(
                {"detail": "Submit either a 'file' upload or a 'text' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = build_upload_document().execute(
                document_type=DocumentType.JOB_OFFER,
                content=content,
                original_filename=filename,
                mime_type=mime_type,
            )
        except DocumentValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if result.needs_processing:
            process_job_document.delay(result.document.id)

        document_row = Document.objects.get(id=result.document.id)
        return Response(DocumentSerializer(document_row).data, status=status.HTTP_202_ACCEPTED)

    @staticmethod
    def _extract_upload(request) -> tuple[bytes | None, str, str]:
        uploaded_file = request.FILES.get("file")
        if uploaded_file is not None:
            content_type = uploaded_file.content_type or "application/octet-stream"
            return uploaded_file.read(), uploaded_file.name, content_type

        text = request.data.get("text") if hasattr(request.data, "get") else None
        if text:
            return text.encode("utf-8"), PASTED_TEXT_PLACEHOLDER_FILENAME, "text/plain"

        return None, "", ""


class JobDetailView(APIView):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, document_type=DocumentType.JOB_OFFER.value)
        return Response(DocumentSerializer(document).data)

    def delete(self, request, document_id):
        get_object_or_404(Document, id=document_id, document_type=DocumentType.JOB_OFFER.value)
        build_delete_document().execute(str(document_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class JobStatusView(APIView):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, document_type=DocumentType.JOB_OFFER.value)
        return Response(DocumentStatusSerializer(document).data)


class JobProfileDetailView(APIView):
    def get(self, request, document_id):
        document = get_object_or_404(Document, id=document_id, document_type=DocumentType.JOB_OFFER.value)

        profile = None
        if document.status == ProcessingStatus.PROCESSED.value:
            job_profile = JobProfile.objects.filter(document=document).first()
            if job_profile is not None:
                profile = JobProfileSerializer(job_profile).data

        return Response({"document_id": str(document.id), "status": document.status, "profile": profile})
