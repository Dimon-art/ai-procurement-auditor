from pathlib import Path
from tempfile import gettempdir
from unittest.mock import Mock, patch

import requests
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField, OCRResult
from apps.documents.services.document_ocr import process_document_ocr
from apps.documents.services.failing_ocr import FailingOCRService
from apps.documents.services.mock_ocr import MockOCRService
from apps.documents.services.ocr_factory import get_ocr_service
from apps.documents.services.yandex_ocr import YandexOCRService
from apps.users.models import UserProfile


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

    @patch(
        "apps.documents.services.document_ocr."
        "extract_and_save_document_fields"
    )
    def test_successful_ocr_extracts_document_fields(
        self,
        mock_extract_fields,
    ):
        result = process_document_ocr(
            self.document,
            MockOCRService(),
        )

        mock_extract_fields.assert_called_once_with(result)

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
    def test_recognize_raises_on_timeout(
        self,
        mock_post,
    ):
        mock_post.side_effect = requests.Timeout(
            "Yandex OCR request timed out"
        )

        service = YandexOCRService()

        with self.assertRaises(requests.Timeout):
            service.recognize(
                self.document_path,
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


class DocumentUploadViewTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Upload Test Company",
        )

    @patch(
        "apps.documents.views.get_ocr_service",
        return_value=MockOCRService(),
    )
    def test_successful_upload_shows_ocr_text(
        self,
        mock_get_ocr_service,
    ):
        response = self.client.post(
            "/documents/upload/",
            {
                "company": self.company.id,
                "document": SimpleUploadedFile(
                    "success_invoice.pdf",
                    b"fake pdf content",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mock OCR text")

        document = Document.objects.get(
            filename="success_invoice.pdf"
        )

        self.assertEqual(
            document.file_size,
            len(b"fake pdf content"),
        )

        self.assertEqual(
            len(document.file_hash),
            64,
        )

    @patch(
        "apps.documents.views.process_document_ocr"
    )
    @patch(
        "apps.documents.views.get_ocr_service",
        return_value=MockOCRService(),
    )
    def test_successful_upload_shows_extracted_fields(
        self,
        mock_get_ocr_service,
        mock_process_document_ocr,
    ):
        def process_ocr(document, ocr_service):
            OCRResult.objects.create(
                document=document,
                provider="mock",
                raw_text="Recognized text",
                confidence=1.0,
            )

            DocumentField.objects.create(
                document=document,
                field_name="supplier_inn",
                raw_value="7704458262",
                normalized_value="7704458262",
                confidence=1.0,
                extraction_method="regex",
            )

            document.status = Document.Status.OCR_COMPLETED
            document.save(
                update_fields=["status", "updated_at"]
            )

        mock_process_document_ocr.side_effect = process_ocr

        response = self.client.post(
            "/documents/upload/",
            {
                "company": self.company.id,
                "document": SimpleUploadedFile(
                    "fields_invoice.pdf",
                    b"fake pdf content",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "supplier_inn")
        self.assertContains(response, "7704458262")

    @patch(
        "apps.documents.views.get_ocr_service",
        return_value=FailingOCRService(),
    )
    def test_ocr_failure_does_not_crash_upload_view(
        self,
        mock_get_ocr_service,
    ):
        response = self.client.post(
            "/documents/upload/",
            {
                "company": self.company.id,
                "document": SimpleUploadedFile(
                    "failed_invoice.pdf",
                    b"fake pdf content",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)

        document = Document.objects.get(
            filename="failed_invoice.pdf"
        )

        self.assertEqual(
            document.status,
            Document.Status.ERROR,
        )


class DocumentListAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="documentapi",
            password="StrongTestPassword123!",
        )

        self.company = Company.objects.create(
            name="Document API Company",
        )

        self.other_company = Company.objects.create(
            name="Other Company",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Document API User",
            role=UserProfile.Role.ACCOUNTANT,
            status=UserProfile.Status.ACTIVE,
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "my_invoice.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="my_invoice.pdf",
            file_size=len(b"fake pdf content"),
        )

        self.other_document = Document.objects.create(
            company=self.other_company,
            original_file=SimpleUploadedFile(
                "other_invoice.pdf",
                b"other pdf content",
                content_type="application/pdf",
            ),
            filename="other_invoice.pdf",
            file_size=len(b"other pdf content"),
        )

    def authenticate(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "documentapi",
                "password": "StrongTestPassword123!",
            },
            format="json",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )

    def test_document_list_requires_authentication(self):
        response = self.client.get(
            reverse("document-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_document_list_returns_only_current_company_documents(self):
        self.authenticate()

        response = self.client.get(
            reverse("document-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(response.data["success"])
        self.assertIsNone(response.data["message"])
        self.assertEqual(
            response.data["errors"],
            [],
        )

        self.assertEqual(
            len(response.data["data"]),
            1,
        )

        self.assertEqual(
            response.data["data"][0]["id"],
            self.document.id,
        )

        self.assertNotEqual(
            response.data["data"][0]["id"],
            self.other_document.id,
        )

class DocumentStatusAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="documentstatus",
            password="StrongTestPassword123!",
        )

        self.company = Company.objects.create(
            name="Document Status Company",
        )

        self.other_company = Company.objects.create(
            name="Other Document Status Company",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Document Status User",
            role=UserProfile.Role.ACCOUNTANT,
            status=UserProfile.Status.ACTIVE,
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "status_invoice.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="status_invoice.pdf",
            file_size=len(b"fake pdf content"),
            status=Document.Status.OCR_PROCESSING,
        )

        self.other_document = Document.objects.create(
            company=self.other_company,
            original_file=SimpleUploadedFile(
                "other_status_invoice.pdf",
                b"other fake pdf content",
                content_type="application/pdf",
            ),
            filename="other_status_invoice.pdf",
            file_size=len(b"other fake pdf content"),
            status=Document.Status.VERIFIED,
        )

    def authenticate(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "documentstatus",
                "password": "StrongTestPassword123!",
            },
            format="json",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )

    def test_document_status_returns_current_status(self):
        self.authenticate()

        response = self.client.get(
            reverse(
                "document-status",
                kwargs={"pk": self.document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data["success"],
        )

        self.assertEqual(
            response.data["data"]["status"],
            Document.Status.OCR_PROCESSING,
        )

    def test_document_status_requires_authentication(self):
        response = self.client.get(
            reverse(
                "document-status",
                kwargs={"pk": self.document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_document_status_does_not_return_other_company_document(self):
        self.authenticate()

        response = self.client.get(
            reverse(
                "document-status",
                kwargs={"pk": self.other_document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            response.data["success"],
        )

        self.assertIsNone(
            response.data["data"],
        )

    def test_document_status_returns_404_for_nonexistent_document(self):
        self.authenticate()

        nonexistent_pk = max(
            self.document.pk,
            self.other_document.pk,
        ) + 1000

        response = self.client.get(
            reverse(
                "document-status",
                kwargs={"pk": nonexistent_pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            response.data["success"],
        )

        self.assertIsNone(
            response.data["data"],
        )

class DocumentRecheckAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="documentrecheck",
            password="StrongTestPassword123!",
        )

        self.company = Company.objects.create(
            name="Document Recheck Company",
        )

        self.other_company = Company.objects.create(
            name="Other Document Recheck Company",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Document Recheck User",
            role=UserProfile.Role.ACCOUNTANT,
            status=UserProfile.Status.ACTIVE,
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "recheck_invoice.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="recheck_invoice.pdf",
            file_size=len(b"fake pdf content"),
            status=Document.Status.OCR_COMPLETED,
        )

        self.other_document = Document.objects.create(
            company=self.other_company,
            original_file=SimpleUploadedFile(
                "other_recheck_invoice.pdf",
                b"other fake pdf content",
                content_type="application/pdf",
            ),
            filename="other_recheck_invoice.pdf",
            file_size=len(b"other fake pdf content"),
            status=Document.Status.OCR_COMPLETED,
        )

    def authenticate(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "documentrecheck",
                "password": "StrongTestPassword123!",
            },
            format="json",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )

    def test_document_recheck_runs_rule_engine(self):
        self.authenticate()

        response = self.client.post(
            reverse(
                "document-recheck",
                kwargs={"pk": self.document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data["success"],
        )

    def test_document_recheck_requires_authentication(self):
        response = self.client.post(
            reverse(
                "document-recheck",
                kwargs={"pk": self.document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_document_recheck_does_not_recheck_other_company_document(self):
        self.authenticate()

        response = self.client.post(
            reverse(
                "document-recheck",
                kwargs={"pk": self.other_document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            response.data["success"],
        )

        self.assertIsNone(
            response.data["data"],
        )

    def test_document_recheck_returns_404_for_nonexistent_document(self):
        self.authenticate()

        nonexistent_pk = max(
            self.document.pk,
            self.other_document.pk,
        ) + 1000

        response = self.client.post(
            reverse(
                "document-recheck",
                kwargs={"pk": nonexistent_pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            response.data["success"],
        )

        self.assertIsNone(
            response.data["data"],
        )

class DocumentReportAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="documentreport",
            password="StrongTestPassword123!",
        )

        self.company = Company.objects.create(
            name="Document Report Company",
        )

        self.other_company = Company.objects.create(
            name="Other Document Report Company",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Document Report User",
            role=UserProfile.Role.ACCOUNTANT,
            status=UserProfile.Status.ACTIVE,
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "report_invoice.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="report_invoice.pdf",
            file_size=len(b"fake pdf content"),
            status=Document.Status.OCR_COMPLETED,
        )

        self.other_document = Document.objects.create(
            company=self.other_company,
            original_file=SimpleUploadedFile(
                "other_report_invoice.pdf",
                b"other fake pdf content",
                content_type="application/pdf",
            ),
            filename="other_report_invoice.pdf",
            file_size=len(b"other fake pdf content"),
            status=Document.Status.OCR_COMPLETED,
        )

    def authenticate(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "documentreport",
                "password": "StrongTestPassword123!",
            },
            format="json",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )

    def test_document_report_returns_report(self):
        self.authenticate()

        response = self.client.get(
            reverse(
                "document-report",
                kwargs={"pk": self.document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data["success"],
        )

        self.assertIn(
            "risk_score",
            response.data["data"],
        )

        self.assertIn(
            "decision",
            response.data["data"],
        )

        self.assertIn(
            "results",
            response.data["data"],
        )

    def test_document_report_requires_authentication(self):
        response = self.client.get(
            reverse(
                "document-report",
                kwargs={"pk": self.document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_document_report_does_not_return_other_company_document(self):
        self.authenticate()

        response = self.client.get(
            reverse(
                "document-report",
                kwargs={"pk": self.other_document.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            response.data["success"],
        )

        self.assertIsNone(
            response.data["data"],
        )

    def test_document_report_returns_404_for_nonexistent_document(self):
        self.authenticate()

        nonexistent_pk = max(
            self.document.pk,
            self.other_document.pk,
        ) + 1000

        response = self.client.get(
            reverse(
                "document-report",
                kwargs={"pk": nonexistent_pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            response.data["success"],
        )

        self.assertIsNone(
            response.data["data"],
        )