from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document
from apps.rules.file_format import FileFormatRule


class FileFormatRuleTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

    def test_rule_passes_for_supported_file_format(self):
        document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="invoice.pdf",
        )

        result = FileFormatRule().evaluate(document)

        self.assertEqual(result.rule_id, "R001")
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.severity, "low")
        self.assertEqual(result.weight, 5)
        self.assertEqual(
            result.details["file_extension"],
            ".pdf",
        )

    def test_rule_fails_for_unsupported_file_format(self):
        document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice.txt",
                b"fake text content",
                content_type="text/plain",
            ),
            filename="invoice.txt",
        )

        result = FileFormatRule().evaluate(document)

        self.assertEqual(result.rule_id, "R001")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.severity, "low")
        self.assertEqual(result.weight, 5)
        self.assertEqual(
            result.details["file_extension"],
            ".txt",
        )