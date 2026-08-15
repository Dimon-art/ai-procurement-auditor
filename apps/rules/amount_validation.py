from decimal import Decimal, InvalidOperation

from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class AmountValidationRule(Rule):
    """
    Validate the total document amount.
    """

    rule_id = "R008"
    rule_name = "Amount Validation"
    severity = "high"
    weight = 30

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        amount_field = (
            document.fields
            .filter(field_name="total_amount")
            .order_by("-id")
            .first()
        )

        if amount_field is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Total amount is missing.",
                details={
                    "total_amount": None,
                },
            )

        amount_value = (
            amount_field.normalized_value
            or amount_field.raw_value
            or ""
        ).strip()

        if not amount_value:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Total amount is empty.",
                details={
                    "total_amount": "",
                },
            )

        try:
            total_amount = Decimal(amount_value)
        except InvalidOperation:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Total amount is invalid.",
                details={
                    "total_amount": amount_value,
                },
            )

        if total_amount <= 0:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Total amount must be greater than zero.",
                details={
                    "total_amount": str(total_amount),
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status="passed",
            severity=self.severity,
            weight=self.weight,
            message="Total amount is valid.",
            details={
                "total_amount": str(total_amount),
            },
        )