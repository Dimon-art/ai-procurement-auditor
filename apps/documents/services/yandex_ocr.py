import base64
import os
from pathlib import Path

import requests

from apps.documents.services.ocr import OCRResponse, OCRService


class YandexOCRService(OCRService):
    """
    OCR adapter for Yandex Vision OCR.
    """

    provider_name = "yandex"

    endpoint = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"

    supported_mime_types = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
        ".pdf": "PDF",
    }

    def __init__(self):
        self.api_key = os.getenv("YANDEX_OCR_API_KEY")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")

        if not self.api_key:
            raise RuntimeError("YANDEX_OCR_API_KEY is not configured")

        if not self.folder_id:
            raise RuntimeError("YANDEX_FOLDER_ID is not configured")

    def recognize(self, file_path: str) -> OCRResponse:
        """
        Send a document to Yandex Vision OCR.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"OCR file does not exist: {file_path}"
            )

        mime_type = self.supported_mime_types.get(
            path.suffix.lower()
        )

        if mime_type is None:
            raise ValueError(
                f"Unsupported OCR file type: {path.suffix}"
            )

        file_content = base64.b64encode(
            path.read_bytes()
        ).decode("ascii")

        payload = {
            "mimeType": mime_type,
            "languageCodes": ["ru", "en"],
            "model": "page",
            "content": file_content,
        }

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json",
        }

        response = requests.post(
            self.endpoint,
            headers=headers,
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        raw_response = response.json()

        text = (
            raw_response
            .get("result", {})
            .get("textAnnotation", {})
            .get("fullText", "")
        )

        return OCRResponse(
            text=text,
            raw_response=raw_response,
            confidence=None,
        )