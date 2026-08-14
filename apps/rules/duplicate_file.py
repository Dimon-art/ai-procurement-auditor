from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class DuplicateFileRule(Rule):
    """
    Detect duplicate files inside the same company by file hash.
    """

    rule_id = "R006"
    rule_name = "Duplicate File Check"
    severity = "high"
    weight = 30

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        file_hash = (
            document.file_hash or ""
        ).strip()

        if not file_hash:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Document file hash is missing.",
                details={
                    "file_hash": "",
                    "duplicate_document_id": None,
                },
            )

        duplicate = (
            Document.objects
            .filter(
                company=document.company,
                file_hash=file_hash,
            )
            .exclude(pk=document.pk)
            .order_by("id")
            .first()
        )

        if duplicate is not None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="Duplicate file was found.",
                details={
                    "file_hash": file_hash,
                    "duplicate_document_id": duplicate.pk,
                },
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status="passed",
            severity=self.severity,
            weight=self.weight,
            message="Duplicate file was not found.",
            details={
                "file_hash": file_hash,
                "duplicate_document_id": None,
            },
        )