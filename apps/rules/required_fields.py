from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class RequiredFieldsRule(Rule):
    rule_id = "R004"
    rule_name = "Required Fields Check"
    severity = "high"
    weight = 30

    required_fields = {
        "document_type",
        "supplier_name",
        "document_number",
        "document_date",
        "currency",
        "total_amount",
        "vat_amount",
    }

    def evaluate(self, document: Document) -> RuleResult:
        existing_fields = set(
            document.fields.values_list(
                "field_name",
                flat=True,
            )
        )

        missing_fields = sorted(
            self.required_fields - existing_fields
        )

        if missing_fields:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Required document fields are missing.",
                details={
                    "missing_fields": missing_fields,
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status="passed",
            severity=self.severity,
            weight=self.weight,
            message="All required document fields are present.",
            details={
                "missing_fields": [],
            },
        )

    def check(self, document: Document) -> RuleResult:
        return self.evaluate(document)