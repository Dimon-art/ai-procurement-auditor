from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField
from apps.rules.required_fields import RequiredFieldsRule


class RequiredFieldsRuleTests(TestCase):
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

    def test_rule_passes_when_all_required_fields_exist(self):
        required_fields = {
            "document_type": "invoice",
            "supplier_name": "Test Supplier",
            "document_number": "123",
            "document_date": "2026-08-13",
            "currency": "RUB",
            "total_amount": "1000.00",
            "vat_amount": "200.00",
        }

        for field_name, value in required_fields.items():
            DocumentField.objects.create(
                document=self.document,
                field_name=field_name,
                raw_value=value,
                normalized_value=value,
                extraction_method="test",
            )

        result = RequiredFieldsRule().check(self.document)

        self.assertEqual(result.rule_id, "R004")
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.weight, 30)
        self.assertEqual(result.details["missing_fields"], [])

    def test_rule_fails_when_required_field_is_missing(self):
        required_fields = {
            "document_type": "invoice",
            "supplier_name": "Test Supplier",
            "document_number": "123",
            "document_date": "2026-08-13",
            "currency": "RUB",
            "total_amount": "1000.00",
        }

        for field_name, value in required_fields.items():
            DocumentField.objects.create(
                document=self.document,
                field_name=field_name,
                raw_value=value,
                normalized_value=value,
                extraction_method="test",
            )

        result = RequiredFieldsRule().check(self.document)

        self.assertEqual(result.rule_id, "R004")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.weight, 30)
        self.assertEqual(
            result.details["missing_fields"],
            ["vat_amount"],
        )