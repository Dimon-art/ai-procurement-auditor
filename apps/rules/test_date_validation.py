from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField
from apps.rules.date_validation import DateValidationRule


class DateValidationRuleTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.rule = DateValidationRule()

    def create_document(
        self,
        document_date: str | None,
    ) -> Document:
        document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice.pdf",
                b"test content",
            ),
            filename="invoice.pdf",
        )

        if document_date is not None:
            DocumentField.objects.create(
                document=document,
                field_name="document_date",
                raw_value=document_date,
                normalized_value=document_date,
                extraction_method="test",
            )

        return document

    def test_returns_passed_for_valid_iso_date(self):
        document = self.create_document(
            date.today().isoformat(),
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")
        self.assertEqual(
            result.details["document_date"],
            date.today().isoformat(),
        )

    def test_returns_passed_for_valid_raw_date_format(self):
        document = self.create_document("15.08.2026")

        field = document.fields.get(
            field_name="document_date",
        )
        field.normalized_value = ""
        field.save()

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "passed")
        self.assertEqual(
            result.details["document_date"],
            "2026-08-15",
        )

    def test_returns_failed_when_date_is_missing(self):
        document = self.create_document(None)

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertIsNone(
            result.details["document_date"]
        )

    def test_returns_failed_when_date_is_empty(self):
        document = self.create_document("")

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["document_date"],
            "",
        )

    def test_returns_failed_for_invalid_date(self):
        document = self.create_document(
            "2026-99-99",
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["document_date"],
            "2026-99-99",
        )

    def test_returns_failed_for_future_date(self):
        future_date = (
            date.today() + timedelta(days=1)
        )

        document = self.create_document(
            future_date.isoformat(),
        )

        result = self.rule.evaluate(document)

        self.assertEqual(result.status, "failed")
        self.assertEqual(
            result.details["document_date"],
            future_date.isoformat(),
        )