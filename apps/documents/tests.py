from pathlib import Path
from tempfile import gettempdir
from unittest.mock import Mock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, OCRResult
from apps.documents.services.document_ocr import process_document_ocr
from apps.documents.services.failing_ocr import FailingOCRService
from apps.documents.services.mock_ocr import MockOCRService
from apps.documents.services.ocr_factory import get_ocr_service
from apps.documents.services.yandex_ocr import YandexOCRService


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


class OCRFactoryTests(TestCase):
    """
    Tests for OCR provider selection.
    """

    @patch(
        "django.conf.settings.OCR_PROVIDER",
        "yandex",
    )
    def test_get_configured_service(self):
        service = get_ocr_service()

        self.assertEqual(
            service.provider_name,
            "yandex",
        )

    @patch(
        "django.conf.settings.OCR_PROVIDER",
        "unknown",
    )
    def test_unknown_provider_raises_error(self):
        with self.assertRaises(ValueError):
            get_ocr_service()


class YandexOCRServiceTests(TestCase):
    """
    Tests for the Yandex OCR adapter.
    """

    @patch.dict(
        "os.environ",
        {
            "YANDEX_OCR_API_KEY": "test-api-key",
            "YANDEX_FOLDER_ID": "test-folder-id",
        },
    )
    @patch(
        "apps.documents.services.yandex_ocr.requests.post"
    )
    def test_recognize_extracts_full_text(
        self,
        mock_post,
    ):
        mock_response = Mock()

        mock_response.json.return_value = {
            "result": {
                "textAnnotation": {
                    "fullText": "Recognized invoice text",
                },
            },
        }

        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        service = YandexOCRService()

        response = service.recognize(
            self.document_path,
        )

        self.assertEqual(
            response.text,
            "Recognized invoice text",
        )

    @property
    def document_path(self):
        return str(
            self._create_test_image()
        )

    def _create_test_image(self):
        path = Path(gettempdir()) / "yandex_ocr_test.png"

        path.write_bytes(
            b"fake image content"
        )

        return path