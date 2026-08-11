from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField, OCRResult
from apps.documents.services.document_fields import (
    extract_and_save_document_fields,
)


class DocumentFieldsServiceTests(TestCase):
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

    def test_extract_and_save_document_fields(self):
        ocr_result = OCRResult.objects.create(
            document=self.document,
            provider="mock",
            raw_text="""
            Счет № 12345
            от 10.08.2026
            Поставщик: ООО "Ромашка"
            ИНН 7704458262
            КПП 770401001
            Итого: 12 345,67
            НДС 20% 2 057,61
            Валюта: RUB
            """,
        )

        saved_fields = extract_and_save_document_fields(
            ocr_result,
        )

        self.assertEqual(
            len(saved_fields),
            9,
        )

        self.assertEqual(
            DocumentField.objects.filter(
                document=self.document,
            ).count(),
            9,
        )

        supplier_name = DocumentField.objects.get(
            document=self.document,
            field_name="supplier_name",
        )

        self.assertEqual(
            supplier_name.normalized_value,
            'ООО "Ромашка"',
        )

        document_number = DocumentField.objects.get(
            document=self.document,
            field_name="document_number",
        )

        self.assertEqual(
            document_number.normalized_value,
            "12345",
        )

        document_date = DocumentField.objects.get(
            document=self.document,
            field_name="document_date",
        )

        self.assertEqual(
            document_date.normalized_value,
            "2026-08-10",
        )

        total_amount = DocumentField.objects.get(
            document=self.document,
            field_name="total_amount",
        )

        self.assertEqual(
            total_amount.normalized_value,
            "12345.67",
        )

        vat_amount = DocumentField.objects.get(
            document=self.document,
            field_name="vat_amount",
        )

        self.assertEqual(
            vat_amount.normalized_value,
            "2057.61",
        )

        currency = DocumentField.objects.get(
            document=self.document,
            field_name="currency",
        )

        self.assertEqual(
            currency.normalized_value,
            "RUB",
        )

    def test_extract_and_save_document_fields_skips_missing_fields(self):
        ocr_result = OCRResult.objects.create(
            document=self.document,
            provider="mock",
            raw_text="""
            Счет № 12345
            от 10.08.2026
            """,
        )

        saved_fields = extract_and_save_document_fields(
            ocr_result,
        )

        self.assertEqual(
            len(saved_fields),
            3,
        )

        self.assertTrue(
            DocumentField.objects.filter(
                document=self.document,
                field_name="document_type",
            ).exists()
        )

        self.assertTrue(
            DocumentField.objects.filter(
                document=self.document,
                field_name="document_number",
            ).exists()
        )

        self.assertTrue(
            DocumentField.objects.filter(
                document=self.document,
                field_name="document_date",
            ).exists()
        )

    def test_extract_and_save_document_fields_does_not_create_duplicates(self):
        ocr_result = OCRResult.objects.create(
            document=self.document,
            provider="mock",
            raw_text="""
            Счет № 12345
            от 10.08.2026
            Итого: 500.00
            """,
        )

        extract_and_save_document_fields(
            ocr_result,
        )

        extract_and_save_document_fields(
            ocr_result,
        )

        self.assertEqual(
            DocumentField.objects.filter(
                document=self.document,
            ).count(),
            4,
        )