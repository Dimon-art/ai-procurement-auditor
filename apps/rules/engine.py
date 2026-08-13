from collections.abc import Iterable

from apps.documents.models import Document
from apps.rules.base import Rule, RuleResult
from apps.rules.result_service import save_rule_result


class RuleEngine:
    """
    Execute document rules and persist their results.
    """

    def __init__(
        self,
        rules: Iterable[Rule],
    ):
        self.rules = list(rules)

    def run(
        self,
        document: Document,
    ) -> list[RuleResult]:
        results = []

        for rule in self.rules:
            result = rule.evaluate(document)

            save_rule_result(
                document,
                result,
            )

            results.append(result)

        return results