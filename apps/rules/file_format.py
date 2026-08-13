from pathlib import Path

from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class FileFormatRule(Rule):
    """
    Validate that the document uses a supported file format.
    """

    rule_id = "R001"
    rule_name = "File Format Validation"
    severity = "low"
    weight = 5

    supported_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".pdf",
    }

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        file_extension = Path(
            document.original_file.name
        ).suffix.lower()

        is_supported = (
            file_extension in self.supported_extensions
        )

        if is_supported:
            status = "passed"
            message = "Document file format is supported."
        else:
            status = "failed"
            message = "Document file format is not supported."

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=status,
            severity=self.severity,
            weight=self.weight,
            message=message,
            details={
                "file_extension": file_extension,
            },
        )