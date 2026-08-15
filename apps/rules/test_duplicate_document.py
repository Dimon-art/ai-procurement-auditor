from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField
from apps.rules.duplicate_document import DuplicateDocumentRule


class DuplicateDocumentRuleTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.other_company = Company.objects.create(
            name="Other Company",
        )

        self.rule = DuplicateDocumentRule()

    def create_document(
        self,
        company,
        filename,
        fields,
    ):
        document = Document.objects.create(
            company=company,
            original_file=SimpleUploadedFile(
                filename,
                b"test content",
            ),
            filename=filename,
        )

        for field_name, value in fields.items():
            DocumentField.objects.create(
                document=document,
                field_name=field_name,
                raw_value=value,
                normalized_value=value,
                extraction_method="test",
            )

        return document

    def test_returns_passed_when_duplicate_does_not_exist(self):
        document = self.create_document(
            company=self.company,
            filename="invoice-1.pdf",
            fields={
                "supplier_inn": "7701234567",
                "document_number": "INV-001",
                "document_date": "2026-08-15",
                "total_amount": "10000.00",
            },
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")
        self.assertIsNone(
            result.details["duplicate_document_id"]
        )

    def test_returns_failed_when_duplicate_exists(self):
        original = self.create_document(
            company=self.company,
            filename="invoice-1.pdf",
            fields={
                "supplier_inn": "7701234567",
                "document_number": "INV-001",
                "document_date": "2026-08-15",
                "total_amount": "10000.00",
            },
        )

        duplicate = self.create_document(
            company=self.company,
            filename="invoice-copy.pdf",
            fields={
                "supplier_inn": "7701234567",
                "document_number": "INV-001",
                "document_date": "2026-08-15",
                "total_amount": "10000.00",
            },
        )

        result = self.rule.evaluate(duplicate)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["duplicate_document_id"],
            original.pk,
        )

    def test_does_not_match_document_from_other_company(self):
        self.create_document(
            company=self.other_company,
            filename="invoice-other.pdf",
            fields={
                "supplier_inn": "7701234567",
                "document_number": "INV-001",
                "document_date": "2026-08-15",
                "total_amount": "10000.00",
            },
        )

        document = self.create_document(
            company=self.company,
            filename="invoice-1.pdf",
            fields={
                "supplier_inn": "7701234567",
                "document_number": "INV-001",
                "document_date": "2026-08-15",
                "total_amount": "10000.00",
            },
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")

    def test_returns_failed_when_required_field_is_missing(self):
        document = self.create_document(
            company=self.company,
            filename="invoice-1.pdf",
            fields={
                "supplier_inn": "7701234567",
                "document_number": "INV-001",
                "document_date": "2026-08-15",
            },
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertIn(
            "total_amount",
            result.details["missing_fields"],
        )

    def test_different_amount_is_not_duplicate(self):
        self.create_document(
            company=self.company,
            filename="invoice-1.pdf",
            fields={
                "supplier_inn": "7701234567",
                "document_number": "INV-001",
                "document_date": "2026-08-15",
                "total_amount": "10000.00",
            },
        )

        document = self.create_document(
            company=self.company,
            filename="invoice-2.pdf",
            fields={
                "supplier_inn": "7701234567",
                "document_number": "INV-001",
                "document_date": "2026-08-15",
                "total_amount": "15000.00",
            },
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")