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

    def test_extract_and_save_document_fields_removes_stale_fields(self):
        DocumentField.objects.create(
            document=self.document,
            field_name="document_number",
            raw_value="ов",
            normalized_value="ов",
            confidence=1.0,
            extraction_method="regex",
        )

        ocr_result = OCRResult.objects.create(
            document=self.document,
            provider="mock",
            raw_text="""
            ИНН 7704458262
            НДС 22/122% 90.16
            """,
        )

        extract_and_save_document_fields(
            ocr_result,
        )

        self.assertFalse(
            DocumentField.objects.filter(
                document=self.document,
                field_name="document_number",
            ).exists()
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

    def test_extract_and_save_real_upd_fields(self):
        ocr_result = OCRResult.objects.create(
            document=self.document,
            provider="yandex",
            raw_text="""
            Универсаль
            ный
            передаточн
            ый документ

            Счет-фактура № 631582 от 25 апреля 2025 г.

            Продавец: Общество с ограниченной ответственностью "ШИНСЕРВИС"

            ИНН/КПП продавца: 7725693620/774950001

            Документ об отгрузке:
            Универсальный передаточный документ № 631582 от 25.04.2025

            Покупатель: ООО "ИСК "БУРСЕРВИС"

            ИНН/КПП покупателя: 7810022206/780601001

            Валюта: наименование, код Российский рубль, 643

            Всего к оплате
            4,00 23
            400,00
            4 680,00
            28 080,00
            """,
        )

        saved_fields = extract_and_save_document_fields(
            ocr_result,
        )

        self.assertEqual(
            len(saved_fields),
            12,
        )

        expected_fields = {
            "supplier_name": (
                'Общество с ограниченной ответственностью '
                '"ШИНСЕРВИС"'
            ),
            "supplier_inn": "7725693620",
            "supplier_kpp": "774950001",
            "buyer_inn": "7810022206",
            "buyer_kpp": "780601001",
            "document_type": "upd",
            "document_number": "631582",
            "document_date": "2025-04-25",
            "amount_without_vat": "23400.00",
            "vat_amount": "4680.00",
            "total_amount": "28080.00",
            "currency": "RUB",
        }

        actual_fields = dict(
            DocumentField.objects.filter(
                document=self.document,
            ).values_list(
                "field_name",
                "normalized_value",
            )
        )

        self.assertEqual(
            actual_fields,
            expected_fields,
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