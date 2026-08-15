def determine_document_decision(
    risk_score: int,
) -> str:
    """
    Determine the final document decision by risk score.
    """

    if risk_score == 0:
        return "ok"

    if risk_score <= 20:
        return "warning"

    if risk_score <= 60:
        return "risk"

    return "manual_review"