from django.test import SimpleTestCase

from apps.rules.registry import get_default_rules


class RuleRegistryTests(SimpleTestCase):
    def test_default_rules_are_returned_in_execution_order(self):
        rules = get_default_rules()

        rule_ids = [
            rule.rule_id
            for rule in rules
        ]

        self.assertEqual(
            rule_ids,
            [
                "R001",
                "R002",
                "R003",
                "R004",
                "R005",
                "R006",
                "R007",
                "R008",
                "R009",
                "R010",
            ],
        )

    def test_default_rule_ids_are_unique(self):
        rules = get_default_rules()

        rule_ids = [
            rule.rule_id
            for rule in rules
        ]

        self.assertEqual(
            len(rule_ids),
            len(set(rule_ids)),
        )