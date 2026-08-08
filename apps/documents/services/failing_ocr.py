from apps.documents.services.ocr import OCRResponse, OCRService


class FailingOCRService(OCRService):
    """
    Test OCR service that always simulates a provider failure.
    """

    provider_name = "failing"

    def recognize(self, file_path: str) -> OCRResponse:
        """
        Simulate an OCR provider failure.
        """
        raise RuntimeError("Mock OCR provider failure")