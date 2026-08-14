from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class FileIntegrityRule(Rule):
    """
    Validate basic document file integrity metadata.
    """

    rule_id = "R002"
    rule_name = "File Integrity Validation"
    severity = "high"
    weight = 30

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        file_exists = bool(
            document.original_file
        )
        file_size = document.file_size
        hash_length = len(
            document.file_hash or ""
        )

        is_valid = (
            file_exists
            and file_size > 0
            and hash_length == 64
        )

        if is_valid:
            status = "passed"
            message = "Document file integrity metadata is valid."
        else:
            status = "failed"
            message = "Document file integrity metadata is invalid."

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=status,
            severity=self.severity,
            weight=self.weight,
            message=message,
            details={
                "file_exists": file_exists,
                "file_size": file_size,
                "hash_length": hash_length,
            },
        )