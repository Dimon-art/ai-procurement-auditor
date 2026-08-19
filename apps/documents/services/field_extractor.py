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

    SELLER_TAX_PATTERN = re.compile(
        r"ИНН/КПП\s+(?:продавца|поставщика)\s*:\s*"
        r"(\d{10}|\d{12})\s*/\s*(\d{9})",
        re.IGNORECASE,
    )

    BUYER_TAX_PATTERN = re.compile(
        r"ИНН/КПП\s+покупателя\s*:\s*"
        r"(\d{10}|\d{12})\s*/\s*(\d{9})",
        re.IGNORECASE,
    )

    SUPPLIER_NAME_PATTERN = re.compile(
        r"^\s*(?:поставщик|продавец)\s*:\s*(.+?)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    UPD_PATTERN = re.compile(
        r"\bупд\b"
        r"|универсаль\s*ный\s+передаточн\s*ый\s+документ"
        r"|универсальный\s+передаточный\s+документ",
        re.IGNORECASE,
    )

    INVOICE_PATTERN = re.compile(
        r"\bсч[её]т(?:-фактура)?\b",
        re.IGNORECASE,
    )

    WAYBILL_PATTERN = re.compile(
        r"\bнакладная\b",
        re.IGNORECASE,
    )

    DOCUMENT_TYPE_PATTERN = re.compile(
        r"\b(сч[её]т|упд|накладная)\b",
        re.IGNORECASE,
    )

    DOCUMENT_NUMBER_PATTERN = re.compile(
        r"\b(?:сч[её]т(?:-фактура)?|упд|накладная|документ)\b"
        r"\s*(?:№|N|No\.?)\s*"
        r"([A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9/_\-]*)",
        re.IGNORECASE,
    )

    DOCUMENT_LINE_DATE_PATTERN = re.compile(
        r"\b(?:сч[её]т(?:-фактура)?|упд|накладная|документ)\b"
        r"[^\n]{0,160}?"
        r"\bот\s*"
        r"(\d{1,2}\.\d{1,2}\.\d{4})",
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

    TOTALS_BLOCK_PATTERN = re.compile(
        r"всего\s+к\s+оплате",
        re.IGNORECASE,
    )

    MONEY_PATTERN = re.compile(
        r"(?<!\d)"
        r"\d{1,3}(?:\s\d{3})*"
        r"(?:[.,]\d{2})"
        r"(?!\d)",
    )

    CURRENCY_PATTERN = re.compile(
        r"\b(RUB|USD|EUR)\b"
        r"|(?<!\w)(₽|\$|€)(?!\w)"
        r"|\b(руб(?:\.|лей|ля|ль)?)(?!\w)",
        re.IGNORECASE,
    )

    @staticmethod
    def _normalize_amount(
        raw_amount: str,
    ) -> str | None:
        normalized_candidate = (
            raw_amount
            .replace(" ", "")
            .replace("\n", "")
            .replace(",", ".")
        )

        try:
            return str(
                Decimal(normalized_candidate)
            )
        except InvalidOperation:
            return None

    def _extract_totals_block_amounts(
        self,
        text: str,
    ) -> list[str]:
        match = self.TOTALS_BLOCK_PATTERN.search(text)

        if match is None:
            return []

        block = text[
            match.end():
            match.end() + 250
        ]

        block = re.sub(
            r"\s+",
            " ",
            block,
        )

        return self.MONEY_PATTERN.findall(
            block,
        )

    def extract_supplier_inn(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        seller_match = self.SELLER_TAX_PATTERN.search(
            text,
        )

        if seller_match is not None:
            inn = seller_match.group(1)
        else:
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

        seller_match = self.SELLER_TAX_PATTERN.search(
            text,
        )

        if seller_match is not None:
            kpp = seller_match.group(2)
        else:
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

    def extract_buyer_inn(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.BUYER_TAX_PATTERN.search(text)

        if match is None:
            return None

        inn = match.group(1)

        return ExtractedField(
            field_name="buyer_inn",
            raw_value=inn,
            normalized_value=inn,
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_buyer_kpp(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.BUYER_TAX_PATTERN.search(text)

        if match is None:
            return None

        kpp = match.group(2)

        return ExtractedField(
            field_name="buyer_kpp",
            raw_value=kpp,
            normalized_value=kpp,
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_supplier_name(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.SUPPLIER_NAME_PATTERN.search(text)

        if match is None:
            return None

        raw_name = match.group(1).strip()
        normalized_name = " ".join(
            raw_name.split()
        )

        if not normalized_name:
            return None

        return ExtractedField(
            field_name="supplier_name",
            raw_value=raw_name,
            normalized_value=normalized_name,
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_document_type(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        upd_match = self.UPD_PATTERN.search(text)

        if upd_match is not None:
            return ExtractedField(
                field_name="document_type",
                raw_value=upd_match.group(0),
                normalized_value="upd",
                confidence=1.0,
                extraction_method="regex",
            )

        invoice_match = self.INVOICE_PATTERN.search(
            text,
        )

        if invoice_match is not None:
            return ExtractedField(
                field_name="document_type",
                raw_value=invoice_match.group(0),
                normalized_value="invoice",
                confidence=1.0,
                extraction_method="regex",
            )

        waybill_match = self.WAYBILL_PATTERN.search(
            text,
        )

        if waybill_match is not None:
            return ExtractedField(
                field_name="document_type",
                raw_value=waybill_match.group(0),
                normalized_value="waybill",
                confidence=1.0,
                extraction_method="regex",
            )

        return None

    def extract_document_number(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.DOCUMENT_NUMBER_PATTERN.search(
            text,
        )

        if match is None:
            return None

        raw_number = match.group(1).strip()

        return ExtractedField(
            field_name="document_number",
            raw_value=raw_number,
            normalized_value=raw_number,
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_document_date(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        match = self.DOCUMENT_LINE_DATE_PATTERN.search(
            text,
        )

        if match is None:
            match = self.DOCUMENT_DATE_PATTERN.search(
                text,
            )

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

    def extract_amount_without_vat(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        amounts = self._extract_totals_block_amounts(
            text,
        )

        if len(amounts) < 3:
            return None

        raw_amount = amounts[-3]

        normalized_amount = self._normalize_amount(
            raw_amount,
        )

        if normalized_amount is None:
            return None

        return ExtractedField(
            field_name="amount_without_vat",
            raw_value=raw_amount,
            normalized_value=normalized_amount,
            confidence=1.0,
            extraction_method="regex",
        )

    def extract_total_amount(
        self,
        text: str,
    ) -> ExtractedField | None:
        if not text:
            return None

        amounts = self._extract_totals_block_amounts(
            text,
        )

        if amounts:
            raw_amount = amounts[-1]
        else:
            match = self.TOTAL_AMOUNT_PATTERN.search(
                text,
            )

            if match is None:
                return None

            raw_amount = match.group(1).strip()

        normalized_amount = self._normalize_amount(
            raw_amount,
        )

        if normalized_amount is None:
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

        amounts = self._extract_totals_block_amounts(
            text,
        )

        if len(amounts) >= 3:
            raw_amount = amounts[-2]
        else:
            match = self.VAT_AMOUNT_PATTERN.search(
                text,
            )

            if match is None:
                return None

            raw_amount = match.group(1).strip()

        normalized_amount = self._normalize_amount(
            raw_amount,
        )

        if normalized_amount is None:
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

        if currency_upper in {
            "RUB",
            "USD",
            "EUR",
        }:
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