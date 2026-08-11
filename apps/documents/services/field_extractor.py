import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation


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

    KPP_PATTERN = re.compile(
        r"\bКПП\s*[:№]?\s*(\d{9})\b",
        re.IGNORECASE,
    )

    DOCUMENT_NUMBER_PATTERN = re.compile(
        r"(?:сч[её]т|упд|накладная|документ)"
        r"\s*(?:№|N|No\.?)?\s*"
        r"([A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9/_\-]*)",
        re.IGNORECASE,
    )

    DOCUMENT_DATE_PATTERN = re.compile(
        r"(?:от|дата)"
        r"\s*[:№]?\s*"
        r"(\d{1,2}\.\d{1,2}\.\d{4})",
        re.IGNORECASE,
    )

    TOTAL_AMOUNT_PATTERN = re.compile(
        r"(?:итого|к\s+оплате)"
        r"\s*:?\s*"
        r"(\d[\d\s]*(?:[.,]\d{1,2})?)",
        re.IGNORECASE,
    )

    VAT_AMOUNT_PATTERN = re.compile(
        r"(?:ндс(?:\s+\d{1,2}(?:/\d{3})?%?)?)"
        r"\s*:?\s*"
        r"(\d[\d\s]*(?:[.,]\d{1,2})?)",
        re.IGNORECASE,
    )

    CURRENCY_PATTERN = re.compile(
        r"\b(RUB|USD|EUR)\b"
        r"|(?<!\w)(₽|\$|€)(?!\w)"
        r"|\b(руб(?:\.|лей|ля|ль)?)(?!\w)",
        re.IGNORECASE,
    )

    def extract_supplier_inn(
        self,
        text: str,
    ) -> ExtractedField | None:
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

    def extract_supplier_kpp(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.KPP_PATTERN.search(text)

        if match is None:
            return None

        kpp = match.group(1)

        return ExtractedField(
            field_name="supplier_kpp",
            raw_value=kpp,
            normalized_value=kpp,
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_document_number(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.DOCUMENT_NUMBER_PATTERN.search(text)

        if match is None:
            return None

        raw_number = match.group(1)

        return ExtractedField(
            field_name="document_number",
            raw_value=raw_number,
            normalized_value=raw_number.strip(),
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_document_date(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.DOCUMENT_DATE_PATTERN.search(text)

        if match is None:
            return None

        raw_date = match.group(1)

        try:
            parsed_date = datetime.strptime(
                raw_date,
                "%d.%m.%Y",
            )
        except ValueError:
            return None

        return ExtractedField(
            field_name="document_date",
            raw_value=raw_date,
            normalized_value=parsed_date.date().isoformat(),
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_total_amount(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.TOTAL_AMOUNT_PATTERN.search(text)

        if match is None:
            return None

        raw_amount = match.group(1).strip()

        normalized_candidate = (
            raw_amount
            .replace(" ", "")
            .replace(",", ".")
        )

        try:
            normalized_amount = str(
                Decimal(normalized_candidate)
            )
        except InvalidOperation:
            return None

        return ExtractedField(
            field_name="total_amount",
            raw_value=raw_amount,
            normalized_value=normalized_amount,
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_vat_amount(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.VAT_AMOUNT_PATTERN.search(text)

        if match is None:
            return None

        raw_amount = match.group(1).strip()

        normalized_candidate = (
            raw_amount
            .replace(" ", "")
            .replace(",", ".")
        )

        try:
            normalized_amount = str(
                Decimal(normalized_candidate)
            )
        except InvalidOperation:
            return None

        return ExtractedField(
            field_name="vat_amount",
            raw_value=raw_amount,
            normalized_value=normalized_amount,
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_currency(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.CURRENCY_PATTERN.search(text)

        if match is None:
            return None

        raw_currency = match.group(0)
        currency_upper = raw_currency.upper()

        if currency_upper in {"RUB", "USD", "EUR"}:
            normalized_currency = currency_upper
        elif raw_currency == "$":
            normalized_currency = "USD"
        elif raw_currency == "€":
            normalized_currency = "EUR"
        else:
            normalized_currency = "RUB"

        return ExtractedField(
            field_name="currency",
            raw_value=raw_currency,
            normalized_value=normalized_currency,
            confidence=1.0,
            extraction_method="regex",
        )