from apps.documents.services.ocr import OCRResponse, OCRService


class MockOCRService(OCRService):
    """
    Тестовый OCR-сервис для разработки и автоматических тестов.
    """

    def recognize(self, file_path: str) -> OCRResponse:
        """
        Возвращает заранее подготовленный результат без внешнего API.
        """
        return OCRResponse(
            text="Mock OCR text",
            raw_response={
                "provider": "mock",
                "file_path": file_path,
            },
            confidence=1.0,
        )