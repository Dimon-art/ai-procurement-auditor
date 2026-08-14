from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document
from apps.rules.file_integrity import FileIntegrityRule


class FileIntegrityRuleTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

    def test_rule_passes_for_valid_file_metadata(self):
        document = Document.objects.create(
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

        result = FileIntegrityRule().evaluate(document)

        self.assertEqual(result.rule_id, "R002")
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.weight, 30)
        self.assertEqual(
            result.details["file_exists"],
            True,
        )
        self.assertEqual(
            result.details["file_size"],
            len(b"fake pdf content"),
        )
        self.assertEqual(
            result.details["hash_length"],
            64,
        )

    def test_rule_fails_when_file_metadata_is_invalid(self):
        document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "empty.pdf",
                b"",
                content_type="application/pdf",
            ),
            filename="empty.pdf",
            file_hash="",
            file_size=0,
        )

        result = FileIntegrityRule().evaluate(document)

        self.assertEqual(result.rule_id, "R002")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.weight, 30)
        self.assertEqual(
            result.details["file_size"],
            0,
        )
        self.assertEqual(
            result.details["hash_length"],
            0,
        )