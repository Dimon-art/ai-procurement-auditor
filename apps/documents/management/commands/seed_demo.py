"""
Management command: seed demo data for the AI Procurement Auditor.

Creates:
- 1 demo company
- 1 demo user (demo / demo12345)
- 6 suppliers (5 unique + 1 with duplicate INN for R005 scenarios)
- 6 documents covering all rule-engine outcomes
- OCR results, extracted fields, and rule engine runs

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # wipe existing demo data first
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.companies.models import Company
from apps.documents.models import (
    Document,
    DocumentField,
    DocumentLineItem,
    OCRResult,
)
from apps.rules.service import run_rule_engine
from apps.suppliers.models import Supplier
from apps.users.models import UserProfile


DEMO_COMPANY_NAME = "ООО Ромашка"
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo12345"
DEMO_EMAIL = "demo@konoplev-web.ru"


class Command(BaseCommand):
    help = "Seed demo data: company, user, suppliers, documents with rule-engine results."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo company and its data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            self._flush()

        company = self._create_company()
        user = self._create_user(company)
        suppliers = self._create_suppliers(company)
        documents = self._create_documents(company, suppliers)

        for document in documents:
            run_rule_engine(document)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Company: {company.name} (id={company.pk}). "
            f"User: {user.username} / {DEMO_PASSWORD}. "
            f"Suppliers: {len(suppliers)}. Documents: {len(documents)}."
        ))

    # ---- cleanup ---------------------------------------------------------

    def _flush(self):
        Document.objects.filter(company__name=DEMO_COMPANY_NAME).delete()
        Supplier.objects.filter(company__name=DEMO_COMPANY_NAME).delete()
        UserProfile.objects.filter(company__name=DEMO_COMPANY_NAME).delete()
        User.objects.filter(username=DEMO_USERNAME).delete()
        Company.objects.filter(name=DEMO_COMPANY_NAME).delete()
        self.stdout.write(self.style.WARNING("Existing demo data deleted."))

    # ---- core entities ---------------------------------------------------

    def _create_company(self) -> Company:
        company, _ = Company.objects.get_or_create(name=DEMO_COMPANY_NAME)
        return company

    def _create_user(self, company: Company) -> User:
        user, created = User.objects.get_or_create(
            username=DEMO_USERNAME,
            defaults={
                "email": DEMO_EMAIL,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "company": company,
                "full_name": "Демо Пользователь",
                "role": UserProfile.Role.COMPANY_ADMIN,
                "status": UserProfile.Status.ACTIVE,
            },
        )
        return user

    # ---- suppliers -------------------------------------------------------

    def _create_suppliers(self, company: Company) -> dict[str, Supplier]:
        specs = [
            {
                "legal_name": 'ООО "ТехноСнаб"',
                "inn": "7701234567",
                "kpp": "770101001",
                "bank_account": "40702810400000012345",
                "bik": "044525225",
            },
            {
                "legal_name": 'АО "ПромКомплект"',
                "inn": "7802345678",
                "kpp": "780201001",
                "bank_account": "40702810500000023456",
                "bik": "044525226",
            },
            {
                "legal_name": 'ООО "СтройРесурс"',
                "inn": "5003456789",
                "kpp": "500301001",
                "bank_account": "40702810600000034567",
                "bik": "044525227",
            },
            {
                "legal_name": 'ИП Иванов И.И.',
                "inn": "504512345678",
                "kpp": "",
                "bank_account": "40802810700000045678",
                "bik": "044525228",
            },
            {
                "legal_name": 'ООО "ЛогистикПро"',
                "inn": "7704567890",
                "kpp": "770401001",
                "bank_account": "40702810800000056789",
                "bik": "044525229",
            },
        ]

        suppliers: dict[str, Supplier] = {}
        for spec in specs:
            supplier, _ = Supplier.objects.get_or_create(
                company=company,
                inn=spec["inn"],
                defaults={
                    "legal_name": spec["legal_name"],
                    "normalized_name": spec["legal_name"].lower(),
                    "kpp": spec["kpp"],
                    "bank_account": spec["bank_account"],
                    "bik": spec["bik"],
                    "status": Supplier.Status.ACTIVE,
                },
            )
            suppliers[spec["inn"]] = supplier

        return suppliers

    # ---- documents -------------------------------------------------------

    def _create_documents(
        self,
        company: Company,
        suppliers: dict[str, Supplier],
    ) -> list[Document]:
        today = date.today()
        specs = self._document_specs(today)

        documents: list[Document] = []

        for index, spec in enumerate(specs, start=1):
            document = Document.objects.create(
                company=company,
                original_file=f"demo/demo_{index:02d}.pdf",
                filename=spec["filename"],
                file_hash=spec["file_hash"],
                file_size=spec["file_size"],
                status=Document.Status.OCR_COMPLETED,
            )

            OCRResult.objects.create(
                document=document,
                provider="mock",
                raw_text=spec["ocr_text"],
                raw_response={"demo": True},
                confidence=spec["ocr_confidence"],
                processing_time_ms=spec["ocr_time_ms"],
                error_message=spec.get("ocr_error", ""),
            )

            for field_name, value in spec["fields"].items():
                DocumentField.objects.create(
                    document=document,
                    field_name=field_name,
                    raw_value=str(value),
                    normalized_value=str(value),
                    confidence=Decimal("0.95"),
                    extraction_method="mock",
                )

            for line in spec["lines"]:
                DocumentLineItem.objects.create(document=document, **line)

            documents.append(document)

        return documents

    def _document_specs(self, today: date) -> list[dict]:
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        last_month = today - timedelta(days=30)

        base_text = (
            "Счёт на оплату. Поставщик, ИНН, КПП, сумма, НДС, итого. "
            "Реквизиты заполнены корректно, документ распознан полностью."
        )
        low_quality_text = "Сч..т ¹ 12.. ИНН 77..  сум.а"

        # 1. Чистый счёт — все правила должны пройти.
        clean = {
            "filename": "schet_1001_clean.pdf",
            "file_hash": "a" * 64,
            "file_size": 120_000,
            "ocr_text": base_text,
            "ocr_confidence": 0.96,
            "ocr_time_ms": 850,
            "fields": {
                "document_type": "invoice",
                "supplier_name": 'ООО "ТехноСнаб"',
                "supplier_inn": "7701234567",
                "document_number": "1001",
                "document_date": last_week.isoformat(),
                "currency": "RUB",
                "total_amount": "120000.00",
                "vat_amount": "20000.00",
            },
            "lines": [
                {
                    "line_number": 1,
                    "description": "Услуги монтажа",
                    "quantity": Decimal("1"),
                    "unit": "шт",
                    "unit_price": Decimal("100000.00"),
                    "amount_without_vat": Decimal("100000.00"),
                    "vat_rate": Decimal("20"),
                    "vat_amount": Decimal("20000.00"),
                    "total_amount": Decimal("120000.00"),
                },
            ],
        }

        # 2. Дубликат документа №1001 (совпадает с clean по 4 ключевым полям).
        duplicate = {
            "filename": "schet_1001_duplicate.pdf",
            "file_hash": "b" * 64,
            "file_size": 121_000,
            "ocr_text": base_text,
            "ocr_confidence": 0.94,
            "ocr_time_ms": 900,
            "fields": {
                "document_type": "invoice",
                "supplier_name": 'ООО "ТехноСнаб"',
                "supplier_inn": "7701234567",
                "document_number": "1001",
                "document_date": last_week.isoformat(),
                "currency": "RUB",
                "total_amount": "120000.00",
                "vat_amount": "20000.00",
            },
            "lines": [
                {
                    "line_number": 1,
                    "description": "Услуги монтажа",
                    "quantity": Decimal("1"),
                    "unit": "шт",
                    "unit_price": Decimal("100000.00"),
                    "amount_without_vat": Decimal("100000.00"),
                    "vat_rate": Decimal("20"),
                    "vat_amount": Decimal("20000.00"),
                    "total_amount": Decimal("120000.00"),
                },
            ],
        }

        # 3. НДС больше суммы — R010 должен упасть.
        bad_tax = {
            "filename": "schet_1002_bad_vat.pdf",
            "file_hash": "c" * 64,
            "file_size": 130_000,
            "ocr_text": base_text,
            "ocr_confidence": 0.95,
            "ocr_time_ms": 870,
            "fields": {
                "document_type": "invoice",
                "supplier_name": 'АО "ПромКомплект"',
                "supplier_inn": "7802345678",
                "document_number": "1002",
                "document_date": last_week.isoformat(),
                "currency": "RUB",
                "total_amount": "50000.00",
                "vat_amount": "60000.00",
            },
            "lines": [
                {
                    "line_number": 1,
                    "description": "Поставка материалов",
                    "quantity": Decimal("10"),
                    "unit": "шт",
                    "unit_price": Decimal("5000.00"),
                    "amount_without_vat": Decimal("50000.00"),
                    "vat_rate": Decimal("20"),
                    "vat_amount": Decimal("10000.00"),
                    "total_amount": Decimal("60000.00"),
                },
            ],
        }

        # 4. Низкое качество OCR — R003 warning.
        low_ocr = {
            "filename": "schet_1003_low_ocr.pdf",
            "file_hash": "d" * 64,
            "file_size": 95_000,
            "ocr_text": "",
            "ocr_confidence": 0.42,
            "ocr_time_ms": 1500,
            "ocr_error": "OCR timeout: provider returned no data",
            "fields": {
                "document_type": "invoice",
                "supplier_name": 'ООО "СтройРесурс"',
                "supplier_inn": "5003456789",
                "document_number": "1003",
                "document_date": last_month.isoformat(),
                "currency": "RUB",
                "total_amount": "15000.00",
                "vat_amount": "2500.00",
            },
            "lines": [],
        }

        # 5. Отсутствует обязательное поле supplier_name — R004 failed.
        missing_field = {
            "filename": "schet_1004_missing_field.pdf",
            "file_hash": "e" * 64,
            "file_size": 110_000,
            "ocr_text": base_text,
            "ocr_confidence": 0.93,
            "ocr_time_ms": 890,
            "fields": {
                "document_type": "invoice",
                "supplier_inn": "504512345678",
                "document_number": "1004",
                "document_date": yesterday.isoformat(),
                "currency": "RUB",
                "total_amount": "80000.00",
                "vat_amount": "13333.33",
            },
            "lines": [],
        }

        # 6. Несуществующий поставщик — R005 failed.
        unknown_supplier = {
            "filename": "schet_1005_unknown_supplier.pdf",
            "file_hash": "f" * 64,
            "file_size": 105_000,
            "ocr_text": base_text,
            "ocr_confidence": 0.90,
            "ocr_time_ms": 920,
            "fields": {
                "document_type": "invoice",
                "supplier_name": 'ООО "Неизвестная Компания"',
                "supplier_inn": "9999999999",
                "document_number": "1005",
                "document_date": yesterday.isoformat(),
                "currency": "RUB",
                "total_amount": "30000.00",
                "vat_amount": "5000.00",
            },
            "lines": [],
        }

        return [
            clean,
            duplicate,
            bad_tax,
            low_ocr,
            missing_field,
            unknown_supplier,
        ]
