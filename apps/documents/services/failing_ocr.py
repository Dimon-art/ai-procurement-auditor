from apps.documents.services.ocr import OCRResponse, OCRService


class FailingOCRService(OCRService):
    """
    Тестовый OCR-сервис, который всегда завершается ошибкой.
    """

    def recognize(self, file_path: str) -> OCRResponse:
        """
        Имитирует сбой внешнего OCR-провайдера.
        """
        raise RuntimeError("Mock OCR provider failure")