from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class OCRResponse:
    """
    Нормализованный результат OCR-распознавания.
    """

    text: str
    raw_response: dict[str, Any]
    confidence: float | None = None


class OCRService(ABC):
    """
    Базовый интерфейс для OCR-провайдеров.
    """

    @abstractmethod
    def recognize(self, file_path: str) -> OCRResponse:
        """
        Распознаёт документ и возвращает нормализованный OCR-результат.
        """
        raise NotImplementedError