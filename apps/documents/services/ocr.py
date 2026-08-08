from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class OCRResponse:
    """
    Normalized result returned by an OCR provider.
    """

    text: str
    raw_response: dict[str, Any]
    confidence: float | None = None


class OCRService(ABC):
    """
    Base interface for OCR providers.
    """

    provider_name: str

    @abstractmethod
    def recognize(self, file_path: str) -> OCRResponse:
        """
        Recognize a document and return a normalized OCR result.
        """
        raise NotImplementedError