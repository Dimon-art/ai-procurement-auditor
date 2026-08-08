import time

from apps.documents.models import Document, OCRResult
from apps.documents.services.ocr import OCRService


def process_document_ocr(
    document: Document,
    ocr_service: OCRService,
) -> OCRResult:
    """
    Run OCR for a document and persist the result.
    """

    document.status = Document.Status.OCR_PROCESSING
    document.save(update_fields=["status", "updated_at"])

    started_at = time.perf_counter()

    try:
        response = ocr_service.recognize(document.original_file.path)

        processing_time_ms = int(
            (time.perf_counter() - started_at) * 1000
        )

        ocr_result = OCRResult.objects.create(
            document=document,
            provider=ocr_service.provider_name,
            raw_text=response.text,
            raw_response=response.raw_response,
            confidence=response.confidence,
            processing_time_ms=processing_time_ms,
        )

        document.status = Document.Status.OCR_COMPLETED
        document.save(update_fields=["status", "updated_at"])

        return ocr_result

    except Exception as exc:
        processing_time_ms = int(
            (time.perf_counter() - started_at) * 1000
        )

        OCRResult.objects.create(
            document=document,
            provider=ocr_service.provider_name,
            processing_time_ms=processing_time_ms,
            error_message=str(exc),
        )

        document.status = Document.Status.ERROR
        document.save(update_fields=["status", "updated_at"])

        raise