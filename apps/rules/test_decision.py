from django.test import SimpleTestCase

from apps.rules.decision import determine_document_decision


class DocumentDecisionTests(SimpleTestCase):
    def test_zero_score_returns_ok(self):
        self.assertEqual(
            determine_document_decision(0),
            "ok",
        )

    def test_score_one_returns_warning(self):
        self.assertEqual(
            determine_document_decision(1),
            "warning",
        )

    def test_score_twenty_returns_warning(self):
        self.assertEqual(
            determine_document_decision(20),
            "warning",
        )

    def test_score_twenty_one_returns_risk(self):
        self.assertEqual(
            determine_document_decision(21),
            "risk",
        )

    def test_score_sixty_returns_risk(self):
        self.assertEqual(
            determine_document_decision(60),
            "risk",
        )

    def test_score_sixty_one_returns_manual_review(self):
        self.assertEqual(
            determine_document_decision(61),
            "manual_review",
        )