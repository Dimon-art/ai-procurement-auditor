from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, OCRResult
from apps.rules.ocr_quality import OCRQualityRule


class OCRQualityRuleTests(TestCase):
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
            file_hash="a" * 64,
            file_size=len(b"fake pdf content"),
        )

    def test_rule_passes_when_text_exists_and_confidence_is_unknown(self):
        OCRResult.objects.create(
            document=self.document,
            provider="yandex",
            raw_text="Invoice number 123",
            confidence=None,
            error_message="",
        )

        result = OCRQualityRule().evaluate(self.document)

        self.assertEqual(result.rule_id, "R003")
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.severity, "medium")

    def test_rule_fails_when_ocr_has_error(self):
        OCRResult.objects.create(
            document=self.document,
            provider="yandex",
            raw_text="",
            confidence=None,
            error_message="OCR provider failure",
        )

        result = OCRQualityRule().evaluate(self.document)

        self.assertEqual(result.rule_id, "R003")
        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["error_message"],
            "OCR provider failure",
        )

    def test_rule_fails_when_ocr_text_is_empty(self):
        OCRResult.objects.create(
            document=self.document,
            provider="yandex",
            raw_text="",
            confidence=None,
            error_message="",
        )

        result = OCRQualityRule().evaluate(self.document)

        self.assertEqual(result.rule_id, "R003")
        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["text_length"],
            0,
        )