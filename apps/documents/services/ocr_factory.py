from django.conf import settings

from apps.documents.services.mock_ocr import MockOCRService
from apps.documents.services.ocr import OCRService
from apps.documents.services.yandex_ocr import YandexOCRService


def get_ocr_service() -> OCRService:
    """
    Create OCR service from Django settings.
    """

    providers = {
        "mock": MockOCRService,
        "yandex": YandexOCRService,
    }

    provider_name = settings.OCR_PROVIDER

    service_class = providers.get(provider_name)

    if service_class is None:
        raise ValueError(
            f"Unsupported OCR provider: {provider_name}"
        )

    return service_class()