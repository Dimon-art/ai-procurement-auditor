from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField
from apps.rules.engine import RuleEngine
from apps.rules.models import CheckResult
from apps.rules.required_fields import RequiredFieldsRule


class RuleEngineTests(TestCase):
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

    def test_engine_runs_rule_and_saves_result(self):
        required_fields = {
            "document_type": "invoice",
            "supplier_name": "Test Supplier",
            "document_number": "123",
            "document_date": "2026-08-13",
            "currency": "RUB",
            "total_amount": "1000.00",
            "vat_amount": "200.00",
        }

        for field_name, value in required_fields.items():
            DocumentField.objects.create(
                document=self.document,
                field_name=field_name,
                raw_value=value,
                normalized_value=value,
                extraction_method="test",
            )

        engine = RuleEngine(
            rules=[
                RequiredFieldsRule(),
            ]
        )

        results = engine.run(
            self.document,
        )

        self.assertEqual(
            len(results),
            1,
        )

        self.assertEqual(
            results[0].rule_id,
            "R004",
        )

        self.assertEqual(
            results[0].status,
            "passed",
        )

        self.assertEqual(
            CheckResult.objects.count(),
            1,
        )

        check_result = CheckResult.objects.get()

        self.assertEqual(
            check_result.rule_id,
            "R004",
        )

        self.assertEqual(
            check_result.status,
            CheckResult.Status.PASSED,
        )