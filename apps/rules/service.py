from dataclasses import dataclass

from apps.documents.models import Document
from apps.rules.base import RuleResult
from apps.rules.decision import determine_document_decision
from apps.rules.engine import RuleEngine
from apps.rules.registry import get_default_rules
from apps.rules.risk_score import calculate_risk_score


@dataclass
class RuleEngineReport:
    results: list[RuleResult]
    risk_score: int
    decision: str


def run_rule_engine(
    document: Document,
) -> RuleEngineReport:
    """
    Run the default MVP rules and return the final rule engine report.
    """

    engine = RuleEngine(
        rules=get_default_rules(),
    )

    results = engine.run(
        document,
    )

    risk_score = calculate_risk_score(
        document,
    )

    decision = determine_document_decision(
        risk_score,
    )

    return RuleEngineReport(
        results=results,
        risk_score=risk_score,
        decision=decision,
    )