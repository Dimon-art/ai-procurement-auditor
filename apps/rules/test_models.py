from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document
from apps.rules.models import CheckResult


class CheckResultModelTests(TestCase):
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

    def test_check_result_can_be_saved(self):
        result = CheckResult.objects.create(
            document=self.document,
            rule_id="R004",
            status=CheckResult.Status.FAILED,
            severity="high",
            score=30,
            actual_value={
                "missing_fields": ["vat_amount"],
            },
            expected_value={
                "required_fields_count": 7,
            },
            explanation="Required document fields are missing.",
            evidence={
                "missing_fields": ["vat_amount"],
            },
        )

        self.assertEqual(result.document, self.document)
        self.assertEqual(result.rule_id, "R004")
        self.assertEqual(result.status, CheckResult.Status.FAILED)
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.score, 30)
        self.assertEqual(
            result.actual_value,
            {"missing_fields": ["vat_amount"]},
        )
        self.assertEqual(
            result.evidence,
            {"missing_fields": ["vat_amount"]},
        )