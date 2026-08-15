from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Sum
from django.test import TestCase

from apps.companies.models import Company
from apps.documents.models import Document, DocumentField
from apps.rules.decision import determine_document_decision
from apps.rules.models import CheckResult
from apps.rules.service import run_rule_engine


class RuleEngineServiceTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

        self.document = Document.objects.create(
            company=self.company,
            original_file=SimpleUploadedFile(
                "invoice.pdf",
                b"test content",
                content_type="application/pdf",
            ),
            filename="invoice.pdf",
            file_size=12,
        )

        fields = {
            "document_type": "invoice",
            "supplier_name": "Test Supplier",
            "supplier_inn": "7701234567",
            "document_number": "INV-001",
            "document_date": "2026-08-15",
            "currency": "RUB",
            "total_amount": "12000.00",
            "vat_amount": "2000.00",
        }

        for field_name, value in fields.items():
            DocumentField.objects.create(
                document=self.document,
                field_name=field_name,
                raw_value=value,
                normalized_value=value,
                extraction_method="test",
            )

    def test_run_rule_engine_returns_complete_report(self):
        report = run_rule_engine(
            self.document,
        )

        self.assertEqual(
            len(report.results),
            10,
        )

        self.assertEqual(
            [result.rule_id for result in report.results],
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

        self.assertEqual(
            CheckResult.objects.filter(
                document=self.document,
            ).count(),
            10,
        )

        stored_score = (
            CheckResult.objects
            .filter(document=self.document)
            .aggregate(total=Sum("score"))
        )["total"] or 0

        self.assertEqual(
            report.risk_score,
            stored_score,
        )

        self.assertEqual(
            report.decision,
            determine_document_decision(
                report.risk_score,
            ),
        )