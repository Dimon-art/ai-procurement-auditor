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
        self.assertEqual(result.field_name, "supplier_inn")
        self.assertEqual(result.raw_value, "7704458262")
        self.assertEqual(result.normalized_value, "7704458262")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.extraction_method, "regex")

    def test_extract_supplier_inn_returns_none_when_missing(self):
        text = """
        ООО "Тестовый поставщик"
        Сумма: 500.00
        """

        result = self.extractor.extract_supplier_inn(text)

        self.assertIsNone(result)

    def test_extract_supplier_kpp(self):
        text = """
        ООО "Тестовый поставщик"
        КПП 770401001
        """

        result = self.extractor.extract_supplier_kpp(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.field_name, "supplier_kpp")
        self.assertEqual(result.raw_value, "770401001")
        self.assertEqual(result.normalized_value, "770401001")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.extraction_method, "regex")

    def test_extract_supplier_kpp_with_colon(self):
        text = """
        КПП: 770401001
        """

        result = self.extractor.extract_supplier_kpp(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "770401001")
        self.assertEqual(result.normalized_value, "770401001")

    def test_extract_supplier_kpp_returns_none_for_invalid_length(self):
        text = """
        КПП 77040100
        """

        result = self.extractor.extract_supplier_kpp(text)

        self.assertIsNone(result)

    def test_extract_supplier_kpp_returns_none_when_missing(self):
        text = """
        ООО "Тестовый поставщик"
        ИНН 7704458262
        """

        result = self.extractor.extract_supplier_kpp(text)

        self.assertIsNone(result)

    def test_extract_document_number(self):
        text = """
        ООО "Тестовый поставщик"
        Счет № 12345
        ИНН 7704458262
        """

        result = self.extractor.extract_document_number(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.field_name, "document_number")
        self.assertEqual(result.raw_value, "12345")
        self.assertEqual(result.normalized_value, "12345")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.extraction_method, "regex")

    def test_extract_document_number_with_letters(self):
        text = """
        УПД № А-123/45
        """

        result = self.extractor.extract_document_number(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "А-123/45")
        self.assertEqual(result.normalized_value, "А-123/45")

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
        self.assertEqual(result.field_name, "document_date")
        self.assertEqual(result.raw_value, "10.08.2026")
        self.assertEqual(result.normalized_value, "2026-08-10")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.extraction_method, "regex")

    def test_extract_document_date_with_date_label(self):
        text = """
        Дата: 01.12.2025
        """

        result = self.extractor.extract_document_date(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "01.12.2025")
        self.assertEqual(result.normalized_value, "2025-12-01")

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

    def test_extract_total_amount(self):
        text = """
        Счет № 12345
        Итого: 12 345,67
        """

        result = self.extractor.extract_total_amount(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.field_name, "total_amount")
        self.assertEqual(result.raw_value, "12 345,67")
        self.assertEqual(result.normalized_value, "12345.67")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.extraction_method, "regex")

    def test_extract_total_amount_with_dot(self):
        text = """
        ИТОГО 500.00
        """

        result = self.extractor.extract_total_amount(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "500.00")
        self.assertEqual(result.normalized_value, "500.00")

    def test_extract_total_amount_with_payment_label(self):
        text = """
        К оплате: 1 250,00
        """

        result = self.extractor.extract_total_amount(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "1 250,00")
        self.assertEqual(result.normalized_value, "1250.00")

    def test_extract_total_amount_returns_none_when_missing(self):
        text = """
        ООО "Тестовый поставщик"
        ИНН 7704458262
        """

        result = self.extractor.extract_total_amount(text)

        self.assertIsNone(result)

    def test_extract_vat_amount(self):
        text = """
        НДС: 90,16
        """

        result = self.extractor.extract_vat_amount(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.field_name, "vat_amount")
        self.assertEqual(result.raw_value, "90,16")
        self.assertEqual(result.normalized_value, "90.16")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.extraction_method, "regex")

    def test_extract_vat_amount_with_rate(self):
        text = """
        НДС 20% 1 250,00
        """

        result = self.extractor.extract_vat_amount(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "1 250,00")
        self.assertEqual(result.normalized_value, "1250.00")

    def test_extract_vat_amount_with_fraction_rate(self):
        text = """
        НДС 22/122% 90.16
        """

        result = self.extractor.extract_vat_amount(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "90.16")
        self.assertEqual(result.normalized_value, "90.16")

    def test_extract_vat_amount_returns_none_when_missing(self):
        text = """
        Итого: 500.00
        """

        result = self.extractor.extract_vat_amount(text)

        self.assertIsNone(result)

    def test_extract_currency_rub_code(self):
        text = """
        Валюта: RUB
        """

        result = self.extractor.extract_currency(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.field_name, "currency")
        self.assertEqual(result.raw_value, "RUB")
        self.assertEqual(result.normalized_value, "RUB")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.extraction_method, "regex")

    def test_extract_currency_usd_code(self):
        text = """
        Валюта: USD
        """

        result = self.extractor.extract_currency(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "USD")
        self.assertEqual(result.normalized_value, "USD")

    def test_extract_currency_eur_symbol(self):
        text = """
        Итого: 500 €
        """

        result = self.extractor.extract_currency(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "€")
        self.assertEqual(result.normalized_value, "EUR")

    def test_extract_currency_dollar_symbol(self):
        text = """
        Итого: 500 $
        """

        result = self.extractor.extract_currency(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "$")
        self.assertEqual(result.normalized_value, "USD")

    def test_extract_currency_ruble_word(self):
        text = """
        Итого: 500 руб.
        """

        result = self.extractor.extract_currency(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "руб.")
        self.assertEqual(result.normalized_value, "RUB")

    def test_extract_currency_returns_none_when_missing(self):
        text = """
        Итого: 500.00
        """

        result = self.extractor.extract_currency(text)

        self.assertIsNone(result)
        
    def test_extract_document_type_invoice(self):
        text = """
        Счет № 12345
        """

        result = self.extractor.extract_document_type(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.field_name, "document_type")
        self.assertEqual(result.raw_value, "Счет")
        self.assertEqual(result.normalized_value, "invoice")
        self.assertEqual(result.confidence, 1.0)
        self.assertEqual(result.extraction_method, "regex")

    def test_extract_document_type_upd(self):
        text = """
        УПД № А-123/45
        """

        result = self.extractor.extract_document_type(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "УПД")
        self.assertEqual(result.normalized_value, "upd")

    def test_extract_document_type_waybill(self):
        text = """
        Накладная № 456
        """

        result = self.extractor.extract_document_type(text)

        self.assertIsNotNone(result)
        self.assertEqual(result.raw_value, "Накладная")
        self.assertEqual(result.normalized_value, "waybill")

    def test_extract_document_type_returns_none_when_missing(self):
        text = """
        ООО "Тестовый поставщик"
        ИНН 7704458262
        """

        result = self.extractor.extract_document_type(text)

        self.assertIsNone(result) 