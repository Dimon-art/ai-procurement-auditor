from django.test import SimpleTestCase

from apps.rules.base import Rule, RuleResult


class RuleResultTests(SimpleTestCase):
    def test_rule_result_stores_normalized_result(self):
        result = RuleResult(
            rule_id="R004",
            rule_name="Required Fields Check",
            status="failed",
            severity="high",
            weight=30,
            message="Required fields are missing.",
            details={"missing_fields": ["supplier_inn"]},
        )

        self.assertEqual(result.rule_id, "R004")
        self.assertEqual(result.rule_name, "Required Fields Check")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.weight, 30)
        self.assertEqual(result.message, "Required fields are missing.")
        self.assertEqual(
            result.details,
            {"missing_fields": ["supplier_inn"]},
        )

    def test_rule_is_abstract(self):
        class IncompleteRule(Rule):
            rule_id = "R999"
            rule_name = "Incomplete Rule"
            severity = "low"
            weight = 5

        with self.assertRaises(TypeError):
            IncompleteRule()