from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document
from apps.rules.models import CheckResult
from apps.rules.risk_score import calculate_risk_score


class RiskScoreTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice.pdf",
                b"test content",
            ),
            filename="invoice.pdf",
        )

    def test_returns_zero_when_document_has_no_results(self):
        score = calculate_risk_score(
            self.document,
        )

        self.assertEqual(
            score,
            0,
        )

    def test_returns_sum_of_check_result_scores(self):
        CheckResult.objects.create(
            document=self.document,
            rule_id="R004",
            status=CheckResult.Status.FAILED,
            severity="high",
            score=30,
        )

        CheckResult.objects.create(
            document=self.document,
            rule_id="R009",
            status=CheckResult.Status.FAILED,
            severity="medium",
            score=15,
        )

        CheckResult.objects.create(
            document=self.document,
            rule_id="R008",
            status=CheckResult.Status.PASSED,
            severity="high",
            score=0,
        )

        score = calculate_risk_score(
            self.document,
        )

        self.assertEqual(
            score,
            45,
        )

    def test_uses_only_latest_result_for_each_rule(self):
        CheckResult.objects.create(
            document=self.document,
            rule_id="R005",
            status=CheckResult.Status.FAILED,
            severity="high",
            score=30,
        )

        CheckResult.objects.create(
            document=self.document,
            rule_id="R005",
            status=CheckResult.Status.PASSED,
            severity="high",
            score=0,
        )

        CheckResult.objects.create(
            document=self.document,
            rule_id="R009",
            status=CheckResult.Status.FAILED,
            severity="medium",
            score=15,
        )

        score = calculate_risk_score(
            self.document,
        )

        self.assertEqual(
            score,
            15,
        )