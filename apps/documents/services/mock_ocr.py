from apps.documents.services.ocr import OCRResponse, OCRService


class MockOCRService(OCRService):
    """
    Test OCR service for development and automated tests.
    """

    provider_name = "mock"

    def recognize(self, file_path: str) -> OCRResponse:
        """
        Return a predefined result without calling an external API.
        """
        return OCRResponse(
            text="Mock OCR text",
            raw_response={
                "provider": self.provider_name,
                "file_path": file_path,
            },
            confidence=1.0,
        )