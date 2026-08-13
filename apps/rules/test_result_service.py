from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document
from apps.rules.base import RuleResult
from apps.rules.models import CheckResult
from apps.rules.result_service import save_rule_result


class SaveRuleResultTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice_test.pdf",
                b"fake pdf content",
                content_type="application/pdf",
            ),
            filename="invoice_test.pdf",
        )

    def test_save_rule_result_creates_check_result(self):
        rule_result = RuleResult(
            rule_id="R004",
            rule_name="Required Fields Check",
            status="failed",
            severity="high",
            weight=30,
            message="Required document fields are missing.",
            details={
                "missing_fields": ["vat_amount"],
            },
        )

        check_result = save_rule_result(
            self.document,
            rule_result,
        )

        self.assertEqual(
            CheckResult.objects.count(),
            1,
        )

        self.assertEqual(
            check_result.document,
            self.document,
        )

        self.assertEqual(
            check_result.rule_id,
            "R004",
        )

        self.assertEqual(
            check_result.status,
            CheckResult.Status.FAILED,
        )

        self.assertEqual(
            check_result.severity,
            "high",
        )

        self.assertEqual(
            check_result.score,
            30,
        )

        self.assertEqual(
            check_result.explanation,
            "Required document fields are missing.",
        )

        self.assertEqual(
            check_result.evidence,
            {
                "missing_fields": ["vat_amount"],
            },
        )