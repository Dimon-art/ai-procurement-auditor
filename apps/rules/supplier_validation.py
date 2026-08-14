from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult
from apps.suppliers.models import Supplier


class SupplierValidationRule(Rule):
    """
    Validate document supplier against company supplier master data.
    """

    rule_id = "R005"
    rule_name = "Supplier Validation"
    severity = "high"
    weight = 30

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        supplier_inn_field = (
            document.fields
            .filter(field_name="supplier_inn")
            .order_by("-id")
            .first()
        )

        if supplier_inn_field is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Supplier INN is missing.",
                details={
                    "supplier_inn": None,
                    "supplier_status": None,
                },
            )

        supplier_inn = (
            supplier_inn_field.normalized_value
            or supplier_inn_field.raw_value
            or ""
        ).strip()

        supplier = (
            Supplier.objects
            .filter(
                company=document.company,
                inn=supplier_inn,
            )
            .first()
        )

        if supplier is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Supplier was not found in master data.",
                details={
                    "supplier_inn": supplier_inn,
                    "supplier_status": None,
                },
            )

        if supplier.status != Supplier.Status.ACTIVE:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Supplier is inactive.",
                details={
                    "supplier_inn": supplier_inn,
                    "supplier_status": supplier.status,
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status="passed",
            severity=self.severity,
            weight=self.weight,
            message="Supplier is valid.",
            details={
                "supplier_inn": supplier_inn,
                "supplier_status": supplier.status,
            },
        )