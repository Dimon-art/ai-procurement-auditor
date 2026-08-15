from decimal import Decimal, InvalidOperation

from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class TaxValidationRule(Rule):
    """
    Validate VAT amount against the total document amount.
    """

    rule_id = "R010"
    rule_name = "Tax Validation"
    severity = "medium"
    weight = 15

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        total_amount = self._get_decimal_field(
            document=document,
            field_name="total_amount",
        )

        if total_amount is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Total amount is missing or invalid.",
                details={
                    "total_amount": None,
                    "vat_amount": None,
                },
            )

        vat_amount = self._get_decimal_field(
            document=document,
            field_name="vat_amount",
        )

        if vat_amount is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="VAT amount is missing or invalid.",
                details={
                    "total_amount": str(total_amount),
                    "vat_amount": None,
                },
            )

        if vat_amount < 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="VAT amount cannot be negative.",
                details={
                    "total_amount": str(total_amount),
                    "vat_amount": str(vat_amount),
                },
            )

        if vat_amount > total_amount:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="VAT amount cannot exceed total amount.",
                details={
                    "total_amount": str(total_amount),
                    "vat_amount": str(vat_amount),
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status="passed",
            severity=self.severity,
            weight=self.weight,
            message="VAT amount is valid.",
            details={
                "total_amount": str(total_amount),
                "vat_amount": str(vat_amount),
            },
        )

    def _get_decimal_field(
        self,
        document: Document,
        field_name: str,
    ) -> Decimal | None:
        field = (
            document.fields
            .filter(field_name=field_name)
            .order_by("-id")
            .first()
        )

        if field is None:
            return None

        value = (
            field.normalized_value
            or field.raw_value
            or ""
        ).strip()

        if not value:
            return None

        try:
            return Decimal(value)
        except InvalidOperation:
            return None