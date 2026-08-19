from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.service import create_audit_log
from apps.companies.models import Company
from apps.documents.models import Document
from apps.documents.pipeline_serializers import PipelineHistorySerializer
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
            status=status.HTTP_201_CREATED,
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
                status=status.HTTP_404_NOT_FOUND,
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
                status=status.HTTP_404_NOT_FOUND,
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
                status=status.HTTP_404_NOT_FOUND,
            )

        report = run_rule_engine(
            document,
        )

        create_audit_log(
            company=company,
            user=request.user,
            document=document,
            action="document.recheck",
            entity_type="document",
            entity_id=str(document.pk),
            new_value={
                "risk_score": report.risk_score,
                "decision": report.decision,
            },
            metadata={
                "source": "api",
            },
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
                status=status.HTTP_404_NOT_FOUND,
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


def _get_pipeline_document(request, document_id):
    company = request.user.profile.company

    return Document.objects.filter(
        company=company,
        pk=document_id,
    ).first()


def _run_pipeline(request, document):
    claimed = (
        Document.objects
        .filter(
            pk=document.pk,
            company=document.company,
        )
        .exclude(
            status=Document.Status.OCR_PROCESSING,
        )
        .update(
            status=Document.Status.OCR_PROCESSING,
            updated_at=timezone.now(),
        )
    )

    if claimed == 0:
        return Response(
            {
                "success": False,
                "data": None,
                "message": "Document pipeline is already running.",
                "errors": [],
            },
            status=status.HTTP_409_CONFLICT,
        )

    document.refresh_from_db()

    try:
        ocr_service = get_ocr_service()

        process_document_ocr(
            document,
            ocr_service,
        )

    except Exception:
        return Response(
            {
                "success": False,
                "data": None,
                "message": "Pipeline processing failed.",
                "errors": [],
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    document.refresh_from_db()

    create_audit_log(
        company=document.company,
        user=request.user,
        document=document,
        action="pipeline.run",
        entity_type="document",
        entity_id=str(document.pk),
        new_value={
            "status": document.status,
        },
        metadata={
            "source": "api",
        },
    )

    return Response(
        {
            "success": True,
            "data": {
                "document_id": document.pk,
                "status": document.status,
            },
            "message": None,
            "errors": [],
        }
    )


class PipelineStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        document = _get_pipeline_document(
            request,
            document_id,
        )

        if document is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Document not found.",
                    "errors": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return _run_pipeline(
            request,
            document,
        )


class PipelineStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = _get_pipeline_document(
            request,
            document_id,
        )

        if document is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Document not found.",
                    "errors": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "success": True,
                "data": {
                    "document_id": document.pk,
                    "status": document.status,
                },
                "message": None,
                "errors": [],
            }
        )


class PipelineHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        document = _get_pipeline_document(
            request,
            document_id,
        )

        if document is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Document not found.",
                    "errors": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        history = document.ocr_results.order_by(
            "-created_at",
        )

        serializer = PipelineHistorySerializer(
            history,
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


class PipelineRestartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, document_id):
        document = _get_pipeline_document(
            request,
            document_id,
        )

        if document is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Document not found.",
                    "errors": [],
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return _run_pipeline(
            request,
            document,
        )

class DocumentListPageView(LoginRequiredMixin, ListView):
    model = Document
    template_name = "documents/list.html"
    context_object_name = "documents"

    def get_queryset(self):
        return Document.objects.filter(
            company=self.request.user.profile.company,
        ).order_by("-created_at")


class DocumentDetailPageView(LoginRequiredMixin, DetailView):
    model = Document
    template_name = "documents/detail.html"
    context_object_name = "document"

    def get_queryset(self):
        return Document.objects.filter(
            company=self.request.user.profile.company,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        document = self.object

        context["document_fields"] = document.fields.order_by(
            "field_name",
        )

        context["ocr_result"] = (
            document.ocr_results
            .order_by(
                "-created_at",
                "-id",
            )
            .first()
        )

        latest_check_results = []

        rule_ids = (
            document.check_results
            .values_list(
                "rule_id",
                flat=True,
            )
            .distinct()
        )

        for rule_id in rule_ids:
            latest_result = (
                document.check_results
                .filter(
                    rule_id=rule_id,
                )
                .order_by(
                    "-created_at",
                    "-id",
                )
                .first()
            )

            if latest_result is not None:
                latest_check_results.append(
                    latest_result
                )

        latest_check_results.sort(
            key=lambda result: result.rule_id,
        )

        context["check_results"] = latest_check_results

        context["risk_score"] = calculate_risk_score(
            document,
        )

        context["decision"] = determine_document_decision(
            context["risk_score"],
        )

        return context

class DocumentApprovePageView(LoginRequiredMixin, View):
    def post(self, request, pk):
        document = get_object_or_404(
            Document,
            company=request.user.profile.company,
            pk=pk,
        )

        previous_status = document.status

        document.status = Document.Status.VERIFIED
        document.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        create_audit_log(
            company=document.company,
            user=request.user,
            document=document,
            action="document.approve",
            entity_type="document",
            entity_id=str(document.pk),
            previous_value={
                "status": previous_status,
            },
            new_value={
                "status": document.status,
            },
            metadata={
                "source": "web",
            },
        )

        return redirect(
            "document-detail-page",
            pk=document.pk,
        )

