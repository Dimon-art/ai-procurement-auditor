from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document
from apps.rules.duplicate_file import DuplicateFileRule


class DuplicateFileRuleTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.other_company = Company.objects.create(
            name="Other Company",
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

    def test_rule_fails_when_duplicate_exists_in_same_company(self):
        Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice_copy.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="invoice_copy.pdf",
            file_hash="a" * 64,
            file_size=len(b"fake pdf content"),
        )

        result = DuplicateFileRule().evaluate(
            self.document,
        )

        self.assertEqual(result.rule_id, "R006")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.weight, 30)

    def test_rule_passes_when_same_hash_exists_in_other_company(self):
        Document.objects.create(
            company=self.other_company,
            original_file=SimpleUploadedFile(
                "invoice.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="invoice.pdf",
            file_hash="a" * 64,
            file_size=len(b"fake pdf content"),
        )

        result = DuplicateFileRule().evaluate(
            self.document,
        )

        self.assertEqual(result.rule_id, "R006")
        self.assertEqual(result.status, "passed")

    def test_rule_passes_when_file_hash_is_unique(self):
        result = DuplicateFileRule().evaluate(
            self.document,
        )

        self.assertEqual(result.rule_id, "R006")
        self.assertEqual(result.status, "passed")