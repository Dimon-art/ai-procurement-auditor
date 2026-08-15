from django.db.models import Sum

from apps.documents.models import Document
from apps.rules.models import CheckResult


def calculate_risk_score(
    document: Document,
) -> int:
    """
    Calculate the total risk score for a document.
    """

    result = (
        CheckResult.objects
        .filter(document=document)
        .aggregate(total=Sum("score"))
    )

    return result["total"] or 0