from apps.documents.services.mock_ocr import MockOCRService
from apps.documents.services.ocr import OCRService
from apps.documents.services.yandex_ocr import YandexOCRService


def get_ocr_service(provider_name: str) -> OCRService:
    """
    Create an OCR service by its stable provider name.
    """

    providers = {
        "mock": MockOCRService,
        "yandex": YandexOCRService,
    }

    service_class = providers.get(provider_name)

    if service_class is None:
        raise ValueError(
            f"Unsupported OCR provider: {provider_name}"
        )

    return service_class()