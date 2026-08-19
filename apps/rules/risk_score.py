from apps.documents.models import Document
from apps.rules.models import CheckResult


def calculate_risk_score(
    document: Document,
) -> int:
    """
    Calculate the total risk score using only
    the latest result for each rule.
    """

    latest_scores = []

    rule_ids = (
        CheckResult.objects
        .filter(document=document)
        .values_list("rule_id", flat=True)
        .distinct()
    )

    for rule_id in rule_ids:
        latest_result = (
            CheckResult.objects
            .filter(
                document=document,
                rule_id=rule_id,
            )
            .order_by("-created_at", "-id")
            .first()
        )

        if latest_result is not None:
            latest_scores.append(
                latest_result.score
            )

    return sum(latest_scores)