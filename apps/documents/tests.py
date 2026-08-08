from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, OCRResult
from apps.documents.services.document_ocr import process_document_ocr
from apps.documents.services.failing_ocr import FailingOCRService
from apps.documents.services.mock_ocr import MockOCRService


class DocumentOCRTests(TestCase):
    """
    Tests for the document OCR pipeline.
    """

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice_test.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="invoice_test.pdf",
        )

    def test_successful_ocr_creates_result_and_updates_status(self):
        result = process_document_ocr(
            self.document,
            MockOCRService(),
        )

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            Document.Status.OCR_COMPLETED,
        )

        self.assertEqual(
            OCRResult.objects.count(),
            1,
        )

        self.assertEqual(
            result.raw_text,
            "Mock OCR text",
        )

        self.assertEqual(
            result.confidence,
            1.0,
        )

        self.assertIsNotNone(
            result.processing_time_ms,
        )

        self.assertGreaterEqual(
            result.processing_time_ms,
            0,
        )

    def test_failed_ocr_saves_error_and_updates_status(self):
        with self.assertRaises(RuntimeError):
            process_document_ocr(
                self.document,
                FailingOCRService(),
            )

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            Document.Status.ERROR,
        )

        self.assertEqual(
            OCRResult.objects.count(),
            1,
        )

        result = OCRResult.objects.get()

        self.assertEqual(
            result.provider,
            "failing",
        )

        self.assertEqual(
            result.error_message,
            "Mock OCR provider failure",
        )

        self.assertIsNotNone(
            result.processing_time_ms,
        )

        self.assertGreaterEqual(
            result.processing_time_ms,
            0,
        )