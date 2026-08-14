from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField
from apps.rules.supplier_validation import SupplierValidationRule
from apps.suppliers.models import Supplier


class SupplierValidationRuleTests(TestCase):
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
        )

    def test_rule_passes_when_active_supplier_is_found_by_inn(self):
        Supplier.objects.create(
            company=self.company,
            legal_name="Test Supplier",
            normalized_name="test supplier",
            inn="7701234567",
            kpp="770101001",
            status=Supplier.Status.ACTIVE,
        )

        DocumentField.objects.create(
            document=self.document,
            field_name="supplier_inn",
            raw_value="7701234567",
            normalized_value="7701234567",
            extraction_method="test",
        )

        result = SupplierValidationRule().evaluate(
            self.document,
        )

        self.assertEqual(result.rule_id, "R005")
        self.assertEqual(result.status, "passed")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.weight, 30)

    def test_rule_fails_when_supplier_is_not_found(self):
        DocumentField.objects.create(
            document=self.document,
            field_name="supplier_inn",
            raw_value="7701234567",
            normalized_value="7701234567",
            extraction_method="test",
        )

        result = SupplierValidationRule().evaluate(
            self.document,
        )

        self.assertEqual(result.rule_id, "R005")
        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["supplier_inn"],
            "7701234567",
        )

    def test_rule_fails_when_supplier_is_inactive(self):
        Supplier.objects.create(
            company=self.company,
            legal_name="Inactive Supplier",
            normalized_name="inactive supplier",
            inn="7701234567",
            status=Supplier.Status.INACTIVE,
        )

        DocumentField.objects.create(
            document=self.document,
            field_name="supplier_inn",
            raw_value="7701234567",
            normalized_value="7701234567",
            extraction_method="test",
        )

        result = SupplierValidationRule().evaluate(
            self.document,
        )

        self.assertEqual(result.rule_id, "R005")
        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["supplier_status"],
            Supplier.Status.INACTIVE,
        )

    def test_rule_fails_when_supplier_inn_is_missing(self):
        result = SupplierValidationRule().evaluate(
            self.document,
        )

        self.assertEqual(result.rule_id, "R005")
        self.assertEqual(result.status, "failed")
        self.assertIsNone(
            result.details["supplier_inn"],
        )
