from apps.documents.models import Document
from apps.rules.base import RuleResult
from apps.rules.models import CheckResult


def save_rule_result(
    document: Document,
    result: RuleResult,
) -> CheckResult:
    """
    Persist a normalized rule result for a document.
    """

    return CheckResult.objects.create(
        document=document,
        rule_id=result.rule_id,
        status=result.status,
        severity=result.severity,
        score=(
            result.weight
            if result.status == "failed"
            else 0
        ),
        explanation=result.message,
        evidence=result.details,
    )