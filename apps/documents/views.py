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
from apps.rules.decision import determine_document_decision
from apps.rules.risk_score import calculate_risk_score
from apps.rules.service import run_rule_engine


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


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        company = request.user.profile.company

        document = Document.objects.filter(
            company=company,
            pk=pk,
        ).first()

        if document is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Document not found.",
                    "errors": [],
                },
                status=404,
            )

        serializer = DocumentSerializer(document)

        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": None,
                "errors": [],
            }
        )


class DocumentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        company = request.user.profile.company

        document = Document.objects.filter(
            company=company,
            pk=pk,
        ).first()

        if document is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Document not found.",
                    "errors": [],
                },
                status=404,
            )

        return Response(
            {
                "success": True,
                "data": {
                    "status": document.status,
                },
                "message": None,
                "errors": [],
            }
        )


class DocumentRecheckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        company = request.user.profile.company

        document = Document.objects.filter(
            company=company,
            pk=pk,
        ).first()

        if document is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Document not found.",
                    "errors": [],
                },
                status=404,
            )

        report = run_rule_engine(
            document,
        )

        return Response(
            {
                "success": True,
                "data": {
                    "risk_score": report.risk_score,
                    "decision": report.decision,
                },
                "message": None,
                "errors": [],
            }
        )


class DocumentReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        company = request.user.profile.company

        document = Document.objects.filter(
            company=company,
            pk=pk,
        ).first()

        if document is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Document not found.",
                    "errors": [],
                },
                status=404,
            )

        check_results = document.check_results.order_by(
            "rule_id",
            "created_at",
        )

        risk_score = calculate_risk_score(
            document,
        )

        decision = determine_document_decision(
            risk_score,
        )

        results = [
            {
                "rule_id": result.rule_id,
                "status": result.status,
                "severity": result.severity,
                "score": result.score,
                "actual_value": result.actual_value,
                "expected_value": result.expected_value,
                "explanation": result.explanation,
                "evidence": result.evidence,
                "created_at": result.created_at,
            }
            for result in check_results
        ]

        return Response(
            {
                "success": True,
                "data": {
                    "risk_score": risk_score,
                    "decision": decision,
                    "results": results,
                },
                "message": None,
                "errors": [],
            }
        )