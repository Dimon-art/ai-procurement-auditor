from apps.documents.models import Document, OCRResult
from apps.documents.services.ocr import OCRService


def process_document_ocr(
    document: Document,
    ocr_service: OCRService,
) -> OCRResult:
    """
    Запускает OCR для документа и сохраняет результат.
    """

    document.status = Document.Status.OCR_PROCESSING
    document.save(update_fields=["status", "updated_at"])

    try:
        response = ocr_service.recognize(document.original_file.path)

        ocr_result = OCRResult.objects.create(
            document=document,
            provider=ocr_service.__class__.__name__,
            raw_text=response.text,
            raw_response=response.raw_response,
            confidence=response.confidence,
        )

        document.status = Document.Status.OCR_COMPLETED
        document.save(update_fields=["status", "updated_at"])

        return ocr_result

    except Exception as exc:
        OCRResult.objects.create(
            document=document,
            provider=ocr_service.__class__.__name__,
            error_message=str(exc),
        )

        document.status = Document.Status.ERROR
        document.save(update_fields=["status", "updated_at"])

        raise