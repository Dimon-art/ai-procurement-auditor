from django.test import TestCase

from apps.companies.models import Company
from apps.suppliers.models import Supplier


class SupplierModelTests(TestCase):
    """
    Tests for Supplier master data.
    """

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
        )

    def test_supplier_is_linked_to_company(self):
        supplier = Supplier.objects.create(
            company=self.company,
            legal_name='ООО "Ромашка"',
            normalized_name='ооо "ромашка"',
            inn="7701234567",
            kpp="770101001",
            bank_account="40702810900000000001",
            bik="044525225",
        )

        self.assertEqual(
            supplier.company,
            self.company,
        )

        self.assertEqual(
            supplier.status,
            Supplier.Status.ACTIVE,
        )

        self.assertEqual(
            supplier.inn,
            "7701234567",
        )

        self.assertEqual(
            str(supplier),
            'ООО "Ромашка"',
        )

# Create your tests here.
