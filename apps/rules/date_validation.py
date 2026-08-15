from datetime import date, datetime

from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class DateValidationRule(Rule):
    """
    Validate the document date.
    """

    rule_id = "R009"
    rule_name = "Date Validation"
    severity = "medium"
    weight = 15

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        date_field = (
            document.fields
            .filter(field_name="document_date")
            .order_by("-id")
            .first()
        )

        if date_field is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Document date is missing.",
                details={
                    "document_date": None,
                },
            )

        date_value = (
            date_field.normalized_value
            or date_field.raw_value
            or ""
        ).strip()

        if not date_value:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Document date is empty.",
                details={
                    "document_date": "",
                },
            )

        parsed_date = self._parse_date(date_value)

        if parsed_date is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Document date is invalid.",
                details={
                    "document_date": date_value,
                },
            )

        if parsed_date > date.today():
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Document date cannot be in the future.",
                details={
                    "document_date": parsed_date.isoformat(),
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status="passed",
            severity=self.severity,
            weight=self.weight,
            message="Document date is valid.",
            details={
                "document_date": parsed_date.isoformat(),
            },
        )

    def _parse_date(
        self,
        value: str,
    ) -> date | None:
        formats = (
            "%Y-%m-%d",
            "%d.%m.%Y",
        )

        for date_format in formats:
            try:
                return datetime.strptime(
                    value,
                    date_format,
                ).date()
            except ValueError:
                continue

        return None

        