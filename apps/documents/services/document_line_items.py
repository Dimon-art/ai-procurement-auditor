from apps.documents.models import DocumentLineItem, OCRResult
from apps.documents.services.line_item_extractor import LineItemExtractor


def extract_and_save_document_line_items(
    ocr_result: OCRResult,
) -> list[DocumentLineItem]:
    """
    Extract document line items from OCR text and persist them.

    Existing line items are updated by line number.
    Stale line items that are no longer extracted are removed.
    """

    extractor = LineItemExtractor()

    extracted_items = extractor.extract(
        ocr_result.raw_text,
    )

    saved_items = []
    extracted_line_numbers = set()

    for extracted_item in extracted_items:
        extracted_line_numbers.add(
            extracted_item.line_number
        )

        line_item, _ = DocumentLineItem.objects.update_or_create(
            document=ocr_result.document,
            line_number=extracted_item.line_number,
            defaults={
                "description": extracted_item.description,
                "quantity": extracted_item.quantity,
                "unit": extracted_item.unit,
                "unit_price": extracted_item.unit_price,
                "amount_without_vat": (
                    extracted_item.amount_without_vat
                ),
                "vat_rate": extracted_item.vat_rate,
                "vat_amount": extracted_item.vat_amount,
                "total_amount": extracted_item.total_amount,
                "raw_data": extracted_item.raw_data,
            },
        )

        saved_items.append(
            line_item
        )

    DocumentLineItem.objects.filter(
        document=ocr_result.document,
    ).exclude(
        line_number__in=extracted_line_numbers,
    ).delete()

    return saved_items