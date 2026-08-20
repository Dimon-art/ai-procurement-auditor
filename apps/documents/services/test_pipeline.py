from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, OCRResult
from apps.documents.services.pipeline import process_document
from apps.rules.models import CheckResult


class DocumentPipelineTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="invoice.pdf",
            file_size=16,
        )

    @patch(
        "apps.documents.services.pipeline.get_ocr_service"
    )
    @patch(
        "apps.documents.services.pipeline.run_rule_engine"
    )
    def test_process_document_runs_complete_pipeline(
        self,
        mock_run_rule_engine,
        mock_get_ocr_service,
    ):
        ocr_service = Mock()
        ocr_service.provider_name = "mock"

        ocr_response = Mock()
        ocr_response.text = """
        Счет № 12345
        от 10.08.2026
        Поставщик: ООО "Ромашка"
        ИНН 7704458262
        Итого: 1000.00
        """
        ocr_response.raw_response = {}
        ocr_response.confidence = 0.95

        ocr_service.recognize.return_value = ocr_response
        mock_get_ocr_service.return_value = ocr_service

        report = Mock()
        report.risk_score = 30
        report.decision = "risk"

        mock_run_rule_engine.return_value = report

        result = process_document(
            self.document,
        )

        self.assertEqual(
            result.risk_score,
            30,
        )

        self.assertEqual(
            result.decision,
            "risk",
        )

        self.assertIsNotNone(
            result.ocr_result,
        )

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            Document.Status.VERIFIED,
        )

        self.assertEqual(
            OCRResult.objects.filter(
                document=self.document,
            ).count(),
            1,
        )

        mock_get_ocr_service.assert_called_once()

        mock_run_rule_engine.assert_called_once_with(
            self.document,
        )