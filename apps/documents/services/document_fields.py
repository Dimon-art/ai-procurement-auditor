from apps.documents.models import DocumentField, OCRResult
from apps.documents.services.field_extractor import FieldExtractor


def extract_and_save_document_fields(
    ocr_result: OCRResult,
) -> list[DocumentField]:
    """
    Extract structured fields from OCR text and persist them.
    """

    extractor = FieldExtractor()

    extraction_methods = [
        extractor.extract_supplier_name,
        extractor.extract_supplier_inn,
        extractor.extract_supplier_kpp,
        extractor.extract_document_type,
        extractor.extract_document_number,
        extractor.extract_document_date,
        extractor.extract_total_amount,
        extractor.extract_vat_amount,
        extractor.extract_currency,
    ]

    saved_fields = []

    for extraction_method in extraction_methods:
        extracted_field = extraction_method(
            ocr_result.raw_text,
        )

        if extracted_field is None:
            continue

        document_field, _ = DocumentField.objects.update_or_create(
            document=ocr_result.document,
            field_name=extracted_field.field_name,
            defaults={
                "raw_value": extracted_field.raw_value,
                "normalized_value": extracted_field.normalized_value,
                "confidence": extracted_field.confidence,
                "extraction_method": extracted_field.extraction_method,
            },
        )

        saved_fields.append(document_field)

    return saved_fields
