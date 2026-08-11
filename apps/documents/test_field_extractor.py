from django.test import SimpleTestCase

from apps.documents.services.field_extractor import FieldExtractor


class FieldExtractorTests(SimpleTestCase):
    """
    Tests for deterministic field extraction from OCR text.
    """

    def setUp(self):
        self.extractor = FieldExtractor()

    def test_extract_supplier_inn(self):
        text = """
        ООО "Тестовый поставщик"
        ИНН 7704458262
        Сумма: 500.00
        """

        result = self.extractor.extract_supplier_inn(text)

        self.assertIsNotNone(result)

        self.assertEqual(
            result.field_name,
            "supplier_inn",
        )

        self.assertEqual(
            result.raw_value,
            "7704458262",
        )

        self.assertEqual(
            result.normalized_value,
            "7704458262",
        )

        self.assertEqual(
            result.confidence,
            1.0,
        )

        self.assertEqual(
            result.extraction_method,
            "regex",
        )

    def test_extract_supplier_inn_returns_none_when_missing(self):
        text = """
        ООО "Тестовый поставщик"
        Сумма: 500.00
        """

        result = self.extractor.extract_supplier_inn(text)

        self.assertIsNone(result)

    def test_extract_document_number(self):
        text = """
        ООО "Тестовый поставщик"
        Счет № 12345
        ИНН 7704458262
        """

        result = self.extractor.extract_document_number(text)

        self.assertIsNotNone(result)

        self.assertEqual(
            result.field_name,
            "document_number",
        )

        self.assertEqual(
            result.raw_value,
            "12345",
        )

        self.assertEqual(
            result.normalized_value,
            "12345",
        )

        self.assertEqual(
            result.confidence,
            1.0,
        )

        self.assertEqual(
            result.extraction_method,
            "regex",
        )

    def test_extract_document_number_with_letters(self):
        text = """
        УПД № А-123/45
        """

        result = self.extractor.extract_document_number(text)

        self.assertIsNotNone(result)

        self.assertEqual(
            result.raw_value,
            "А-123/45",
        )

        self.assertEqual(
            result.normalized_value,
            "А-123/45",
        )

    def test_extract_document_number_returns_none_when_missing(self):
        text = """
        ООО "Тестовый поставщик"
        ИНН 7704458262
        """

        result = self.extractor.extract_document_number(text)

        self.assertIsNone(result)

    def test_extract_document_date(self):
        text = """
        Счет № 12345
        от 10.08.2026
        """

        result = self.extractor.extract_document_date(text)

        self.assertIsNotNone(result)

        self.assertEqual(
            result.field_name,
            "document_date",
        )

        self.assertEqual(
            result.raw_value,
            "10.08.2026",
        )

        self.assertEqual(
            result.normalized_value,
            "2026-08-10",
        )

        self.assertEqual(
            result.confidence,
            1.0,
        )

        self.assertEqual(
            result.extraction_method,
            "regex",
        )

    def test_extract_document_date_with_date_label(self):
        text = """
        Дата: 01.12.2025
        """

        result = self.extractor.extract_document_date(text)

        self.assertIsNotNone(result)

        self.assertEqual(
            result.raw_value,
            "01.12.2025",
        )

        self.assertEqual(
            result.normalized_value,
            "2025-12-01",
        )

    def test_extract_document_date_returns_none_for_invalid_date(self):
        text = """
        Дата: 32.13.2026
        """

        result = self.extractor.extract_document_date(text)

        self.assertIsNone(result)

    def test_extract_document_date_returns_none_when_missing(self):
        text = """
        ООО "Тестовый поставщик"
        ИНН 7704458262
        """

        result = self.extractor.extract_document_date(text)

        self.assertIsNone(result)