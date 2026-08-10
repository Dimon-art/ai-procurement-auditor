import re
from dataclasses import dataclass


@dataclass
class ExtractedField:
    field_name: str
    raw_value: str
    normalized_value: str
    confidence: float
    extraction_method: str


class FieldExtractor:
    """
    Deterministic field extractor for OCR text.
    """

    INN_PATTERN = re.compile(
        r"\b(?:ИНН\s*)?(\d{10}|\d{12})\b",
        re.IGNORECASE,
    )

    def extract_supplier_inn(
        self,
        text: str,
    ) -> ExtractedField | None:
        """
        Extract supplier INN from OCR text.
        """

        if not text:
            return None

        match = self.INN_PATTERN.search(text)

        if match is None:
            return None

        inn = match.group(1)

        return ExtractedField(
            field_name="supplier_inn",
            raw_value=inn,
            normalized_value=inn,
            confidence=1.0,
            extraction_method="regex",
        )