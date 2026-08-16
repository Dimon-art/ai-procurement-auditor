from django.shortcuts import render

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.companies.models import Company
from apps.documents.models import Document
from apps.documents.serializers import (
    DocumentSerializer,
    DocumentUploadSerializer,
)
from apps.documents.services.document_ocr import process_document_ocr
from apps.documents.services.file_metadata import calculate_file_metadata
from apps.documents.services.ocr_factory import get_ocr_service


def upload_document(request):
    """
    Upload document and run OCR.
    """

    companies = Company.objects.all()

    if request.method == "POST":
        company_id = request.POST.get("company")
        uploaded_file = request.FILES.get("document")

        company = Company.objects.get(
            id=company_id
        )

        document = Document.objects.create(
            company=company,
            original_file=uploaded_file,
            filename=uploaded_file.name,
        )

        metadata = calculate_file_metadata(
            document.original_file.path
        )

        document.file_hash = metadata.file_hash
        document.file_size = metadata.file_size

        document.save(
            update_fields=[
                "file_hash",
                "file_size",
                "updated_at",
            ]
        )

        ocr_service = get_ocr_service()

        try:
            process_document_ocr(
                document,
                ocr_service,
            )
        except Exception:
            pass

        document.refresh_from_db()

        ocr_result = document.ocr_results.order_by(
            "-created_at"
        ).first()

        document_fields = document.fields.order_by(
            "field_name"
        )

        return render(
            request,
            "documents/upload.html",
            {
                "companies": companies,
                "uploaded_document": document,
                "ocr_result": ocr_result,
                "document_fields": document_fields,
            },
        )

    return render(
        request,
        "documents/upload.html",
        {
            "companies": companies,
        },
    )


class DocumentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.profile.company

        documents = Document.objects.filter(
            company=company,
        ).order_by("-created_at")

        serializer = DocumentSerializer(
            documents,
            many=True,
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": None,
                "errors": [],
            }
        )

    def post(self, request):
        serializer = DocumentUploadSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        uploaded_file = serializer.validated_data[
            "original_file"
        ]

        company = request.user.profile.company

        document = Document.objects.create(
            company=company,
            original_file=uploaded_file,
            filename=uploaded_file.name,
        )

        metadata = calculate_file_metadata(
            document.original_file.path
        )

        document.file_hash = metadata.file_hash
        document.file_size = metadata.file_size

        document.save(
            update_fields=[
                "file_hash",
                "file_size",
                "updated_at",
            ]
        )

        return Response(
            {
                "success": True,
                "data": DocumentSerializer(document).data,
                "message": None,
                "errors": [],
            },
            status=201,
        )