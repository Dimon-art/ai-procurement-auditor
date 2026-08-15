from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField
from apps.rules.tax_validation import TaxValidationRule


class TaxValidationRuleTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.rule = TaxValidationRule()

    def create_document(
        self,
        total_amount: str | None,
        vat_amount: str | None,
    ) -> Document:
        document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice.pdf",
                b"test content",
            ),
            filename="invoice.pdf",
        )

        if total_amount is not None:
            DocumentField.objects.create(
                document=document,
                field_name="total_amount",
                raw_value=total_amount,
                normalized_value=total_amount,
                extraction_method="test",
            )

        if vat_amount is not None:
            DocumentField.objects.create(
                document=document,
                field_name="vat_amount",
                raw_value=vat_amount,
                normalized_value=vat_amount,
                extraction_method="test",
            )

        return document

    def test_returns_passed_for_valid_vat_amount(self):
        document = self.create_document(
            total_amount="12000.00",
            vat_amount="2000.00",
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")
        self.assertEqual(
            result.details["total_amount"],
            "12000.00",
        )
        self.assertEqual(
            result.details["vat_amount"],
            "2000.00",
        )

    def test_returns_passed_for_zero_vat(self):
        document = self.create_document(
            total_amount="10000.00",
            vat_amount="0",
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")

    def test_returns_failed_when_total_amount_is_missing(self):
        document = self.create_document(
            total_amount=None,
            vat_amount="1000.00",
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertIsNone(
            result.details["total_amount"]
        )

    def test_returns_failed_when_vat_amount_is_missing(self):
        document = self.create_document(
            total_amount="10000.00",
            vat_amount=None,
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertIsNone(
            result.details["vat_amount"]
        )

    def test_returns_failed_for_negative_vat(self):
        document = self.create_document(
            total_amount="10000.00",
            vat_amount="-100.00",
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["vat_amount"],
            "-100.00",
        )

    def test_returns_failed_when_vat_exceeds_total(self):
        document = self.create_document(
            total_amount="1000.00",
            vat_amount="1500.00",
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["vat_amount"],
            "1500.00",
        )

    def test_returns_failed_for_invalid_vat_amount(self):
        document = self.create_document(
            total_amount="10000.00",
            vat_amount="invalid",
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")

    def test_uses_raw_value_when_normalized_value_is_empty(self):
        document = self.create_document(
            total_amount="10000.00",
            vat_amount="2000.00",
        )

        field = document.fields.get(
            field_name="vat_amount",
        )
        field.normalized_value = ""
        field.raw_value = "2000.00"
        field.save()

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")