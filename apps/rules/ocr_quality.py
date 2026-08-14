from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult


class OCRQualityRule(Rule):
    """
    Validate the latest OCR result for a document.
    """

    rule_id = "R003"
    rule_name = "OCR Quality Check"
    severity = "medium"
    weight = 15

    def evaluate(
        self,
        document: Document,
    ) -> RuleResult:
        ocr_result = (
            document.ocr_results
            .order_by("-created_at")
            .first()
        )

        if ocr_result is None:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                status="failed",
                severity=self.severity,
                weight=self.weight,
                message="OCR result is missing.",
                details={
                    "provider": None,
                    "confidence": None,
                    "text_length": 0,
                    "error_message": "OCR result is missing.",
                },
            )

        text = ocr_result.raw_text or ""
        error_message = ocr_result.error_message or ""

        if error_message:
            status = "failed"
            message = "OCR processing completed with an error."
        elif not text.strip():
            status = "failed"
            message = "OCR returned empty text."
        else:
            status = "passed"
            message = "OCR result quality is acceptable."

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.rule_name,
            status=status,
            severity=self.severity,
            weight=self.weight,
            message=message,
            details={
                "provider": ocr_result.provider,
                "confidence": ocr_result.confidence,
                "text_length": len(text),
                "error_message": error_message,
            },
        )