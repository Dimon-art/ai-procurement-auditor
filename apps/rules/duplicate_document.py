from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class DuplicateDocumentRule(Rule):
    """
    Detect logical duplicate documents inside the same company
    by key business fields.
    """

    rule_id = "R007"
    rule_name = "Duplicate Document Check"
    severity = "high"
    weight = 30

    key_fields = (
        "supplier_inn",
        "document_number",
        "document_date",
        "total_amount",
    )

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        document_values = self._get_document_values(document)

        missing_fields = [
            field_name
            for field_name, value in document_values.items()
            if not value
        ]

        if missing_fields:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message=(
                    "Duplicate document check cannot be completed "
                    "because required fields are missing."
                ),
                details={
                    "missing_fields": missing_fields,
                    "duplicate_document_id": None,
                },
            )

        candidates = (
            Document.objects
            .filter(company=document.company)
            .exclude(pk=document.pk)
            .prefetch_related("fields")
            .order_by("id")
        )

        for candidate in candidates:
            candidate_values = self._get_document_values(candidate)

            if candidate_values == document_values:
                return RuleResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    status="failed",
                    severity=self.severity,
                    weight=self.weight,
                    message="Duplicate document was found.",
                    details={
                        **document_values,
                        "duplicate_document_id": candidate.pk,
                    },
                )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status="passed",
            severity=self.severity,
            weight=self.weight,
            message="Duplicate document was not found.",
            details={
                **document_values,
                "duplicate_document_id": None,
            },
        )

    def _get_document_values(
        self,
        document: Document,
    ) -> dict[str, str]:
        fields = {
            field.field_name: field
            for field in document.fields.all()
            if field.field_name in self.key_fields
        }

        values = {}

        for field_name in self.key_fields:
            field = fields.get(field_name)

            if field is None:
                values[field_name] = ""
                continue

            values[field_name] = (
                field.normalized_value
                or field.raw_value
                or ""
            ).strip()

        return values