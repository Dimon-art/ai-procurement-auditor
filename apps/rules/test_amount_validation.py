from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField
from apps.rules.amount_validation import AmountValidationRule


class AmountValidationRuleTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.rule = AmountValidationRule()

    def create_document(
        self,
        total_amount: str | None,
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

        return document

    def test_returns_passed_for_positive_amount(self):
        document = self.create_document("10000.00")

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")
        self.assertEqual(
            result.details["total_amount"],
            "10000.00",
        )

    def test_returns_failed_when_amount_is_missing(self):
        document = self.create_document(None)

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertIsNone(
            result.details["total_amount"]
        )

    def test_returns_failed_when_amount_is_empty(self):
        document = self.create_document("")

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["total_amount"],
            "",
        )

    def test_returns_failed_for_invalid_amount(self):
        document = self.create_document("invalid")

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["total_amount"],
            "invalid",
        )

    def test_returns_failed_for_zero_amount(self):
        document = self.create_document("0")

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["total_amount"],
            "0",
        )

    def test_returns_failed_for_negative_amount(self):
        document = self.create_document("-100.00")

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["total_amount"],
            "-100.00",
        )

    def test_uses_raw_value_when_normalized_value_is_empty(self):
        document = self.create_document("2500.50")

        field = document.fields.get(
            field_name="total_amount",
        )
        field.normalized_value = ""
        field.raw_value = "2500.50"
        field.save()

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")
        self.assertEqual(
            result.details["total_amount"],
            "2500.50",
        )