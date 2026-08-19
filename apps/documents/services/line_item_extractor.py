import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass
class ExtractedLineItem:
    line_number: int
    description: str
    quantity: Decimal | None
    unit: str
    unit_price: Decimal | None
    amount_without_vat: Decimal | None
    vat_rate: Decimal | None
    vat_amount: Decimal | None
    total_amount: Decimal | None
    raw_data: dict


class LineItemExtractor:
    """
    Deterministic extractor for B2B document line items.

    Initial MVP implementation targets OCR text produced from
    Russian invoices and UPD documents.
    """

    LINE_ITEM_PATTERN = re.compile(
        r"^(?P<line_number>\d{1,4})\s*\n"
        r"(?P<description>"
        r"(?:"
        r"[^\n]*[A-Za-zА-Яа-яЁё][^\n]*\n"
        r"){1,4}"
        r")"
        r"(?P<unit_code>\d{3})\s*\n"
        r"(?P<unit>[A-Za-zА-Яа-яЁё.]+)\s*\n"
        r"(?P<quantity>\d[\d\s]*[.,]\d{3,4})\s*\n"
        r"(?P<unit_price>\d[\d\s]*[.,]\d{2})\s*\n"
        r"(?P<amount_without_vat>\d[\d\s]*[.,]\d{2})\s*\n"
        r"(?:без\s+акциза\s*)?"
        r"(?P<vat_rate>\d{1,2}(?:[.,]\d+)?)%\s*\n"
        r"(?P<ocr_vat_amount>\d[\d\s]*[.,]\d{2})\s*\n"
        r"(?P<total_amount>\d[\d\s]*[.,]\d{2})",
        re.IGNORECASE | re.MULTILINE,
    )

    @staticmethod
    def _normalize_decimal(
        raw_value: str,
    ) -> Decimal | None:
        if not raw_value:
            return None

        normalized = (
            raw_value
            .replace(" ", "")
            .replace("\n", "")
            .replace(",", ".")
            .strip()
        )

        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    @staticmethod
    def _normalize_description(
        raw_description: str,
    ) -> str:
        return " ".join(
            raw_description.split()
        )

    def extract(
        self,
        text: str,
    ) -> list[ExtractedLineItem]:
        if not text:
            return []

        extracted_items = []

        for match in self.LINE_ITEM_PATTERN.finditer(text):
            quantity = self._normalize_decimal(
                match.group("quantity"),
            )

            unit_price = self._normalize_decimal(
                match.group("unit_price"),
            )

            amount_without_vat = self._normalize_decimal(
                match.group("amount_without_vat"),
            )

            vat_rate = self._normalize_decimal(
                match.group("vat_rate"),
            )

            ocr_vat_amount = self._normalize_decimal(
                match.group("ocr_vat_amount"),
            )

            total_amount = self._normalize_decimal(
                match.group("total_amount"),
            )

            vat_amount = ocr_vat_amount

            if (
                amount_without_vat is not None
                and total_amount is not None
            ):
                calculated_vat_amount = (
                    total_amount
                    - amount_without_vat
                )

                if calculated_vat_amount >= 0:
                    vat_amount = calculated_vat_amount

            extracted_items.append(
                ExtractedLineItem(
                    line_number=int(
                        match.group("line_number")
                    ),
                    description=self._normalize_description(
                        match.group("description")
                    ),
                    quantity=quantity,
                    unit=match.group("unit").strip(),
                    unit_price=unit_price,
                    amount_without_vat=amount_without_vat,
                    vat_rate=vat_rate,
                    vat_amount=vat_amount,
                    total_amount=total_amount,
                    raw_data={
                        "unit_code": (
                            match.group("unit_code")
                        ),
                        "raw_description": (
                            match.group("description")
                        ),
                        "raw_quantity": (
                            match.group("quantity")
                        ),
                        "raw_unit_price": (
                            match.group("unit_price")
                        ),
                        "raw_amount_without_vat": (
                            match.group(
                                "amount_without_vat"
                            )
                        ),
                        "raw_vat_rate": (
                            match.group("vat_rate")
                        ),
                        "raw_vat_amount": (
                            match.group(
                                "ocr_vat_amount"
                            )
                        ),
                        "raw_total_amount": (
                            match.group("total_amount")
                        ),
                    },
                )
            )

        return extracted_items