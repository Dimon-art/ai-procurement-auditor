from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentLineItem, OCRResult
from apps.documents.services.document_line_items import (
    extract_and_save_document_line_items,
)
from apps.documents.services.line_item_extractor import LineItemExtractor


SAMPLE_UPD_OCR_TEXT = """
1
Автошины SUNFULL 215/70 R16 MONT-PRO
HT782 100H
796
шт
4,000
5 850,00
23 400,00
без акциза 20%
4 680,90
28 080,00
"""


class LineItemExtractorTests(TestCase):
    def test_extracts_upd_line_item(self):
        extractor = LineItemExtractor()

        items = extractor.extract(
            SAMPLE_UPD_OCR_TEXT,
        )

        self.assertEqual(
            len(items),
            1,
        )

        item = items[0]

        self.assertEqual(
            item.line_number,
            1,
        )
        self.assertEqual(
            item.description,
            "Автошины SUNFULL 215/70 R16 MONT-PRO HT782 100H",
        )
        self.assertEqual(
            item.quantity,
            Decimal("4.000"),
        )
        self.assertEqual(
            item.unit,
            "шт",
        )
        self.assertEqual(
            item.unit_price,
            Decimal("5850.00"),
        )
        self.assertEqual(
            item.amount_without_vat,
            Decimal("23400.00"),
        )
        self.assertEqual(
            item.vat_rate,
            Decimal("20"),
        )
        self.assertEqual(
            item.vat_amount,
            Decimal("4680.00"),
        )
        self.assertEqual(
            item.total_amount,
            Decimal("28080.00"),
        )

    def test_preserves_raw_ocr_vat_amount(self):
        extractor = LineItemExtractor()

        items = extractor.extract(
            SAMPLE_UPD_OCR_TEXT,
        )

        self.assertEqual(
            items[0].raw_data["raw_vat_amount"],
            "4 680,90",
        )

        self.assertEqual(
            items[0].vat_amount,
            Decimal("4680.00"),
        )

    def test_empty_text_returns_no_items(self):
        extractor = LineItemExtractor()

        self.assertEqual(
            extractor.extract(""),
            [],
        )


class DocumentLineItemPersistenceTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Line Item Test Company",
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "test_upd.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="test_upd.pdf",
            file_size=len(b"fake pdf content"),
        )

        self.ocr_result = OCRResult.objects.create(
            document=self.document,
            provider="test",
            raw_text=SAMPLE_UPD_OCR_TEXT,
            raw_response={},
        )

    def test_extracts_and_saves_line_item(self):
        saved_items = extract_and_save_document_line_items(
            self.ocr_result,
        )

        self.assertEqual(
            len(saved_items),
            1,
        )

        self.assertEqual(
            DocumentLineItem.objects.filter(
                document=self.document,
            ).count(),
            1,
        )

        item = DocumentLineItem.objects.get(
            document=self.document,
            line_number=1,
        )

        self.assertEqual(
            item.description,
            "Автошины SUNFULL 215/70 R16 MONT-PRO HT782 100H",
        )
        self.assertEqual(
            item.quantity,
            Decimal("4.0000"),
        )
        self.assertEqual(
            item.unit_price,
            Decimal("5850.0000"),
        )
        self.assertEqual(
            item.amount_without_vat,
            Decimal("23400.00"),
        )
        self.assertEqual(
            item.vat_amount,
            Decimal("4680.00"),
        )
        self.assertEqual(
            item.total_amount,
            Decimal("28080.00"),
        )

    def test_repeated_extraction_does_not_create_duplicate(self):
        extract_and_save_document_line_items(
            self.ocr_result,
        )

        extract_and_save_document_line_items(
            self.ocr_result,
        )

        self.assertEqual(
            DocumentLineItem.objects.filter(
                document=self.document,
            ).count(),
            1,
        )

    def test_stale_line_items_are_removed(self):
        DocumentLineItem.objects.create(
            document=self.document,
            line_number=2,
            description="Stale item",
            quantity=Decimal("1"),
            unit="шт",
            unit_price=Decimal("100.00"),
            amount_without_vat=Decimal("100.00"),
            vat_rate=Decimal("20"),
            vat_amount=Decimal("20.00"),
            total_amount=Decimal("120.00"),
            raw_data={},
        )

        extract_and_save_document_line_items(
            self.ocr_result,
        )

        self.assertFalse(
            DocumentLineItem.objects.filter(
                document=self.document,
                line_number=2,
            ).exists()
        )