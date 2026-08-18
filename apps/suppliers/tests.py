from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.companies.models import Company
from apps.suppliers.models import Supplier
from apps.users.models import UserProfile


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


class SupplierListAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="supplierapi",
            password="StrongTestPassword123!",
        )

        self.company = Company.objects.create(
            name="Supplier API Company",
        )

        self.other_company = Company.objects.create(
            name="Other Supplier Company",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Supplier API User",
            role=UserProfile.Role.ACCOUNTANT,
            status=UserProfile.Status.ACTIVE,
        )

        self.supplier = Supplier.objects.create(
            company=self.company,
            legal_name="My Supplier",
            normalized_name="my supplier",
            inn="7701234567",
            kpp="770101001",
            bank_account="40702810900000000001",
            bik="044525225",
        )

        self.other_supplier = Supplier.objects.create(
            company=self.other_company,
            legal_name="Other Supplier",
            normalized_name="other supplier",
            inn="7801234567",
            kpp="780101001",
            bank_account="40702810900000000002",
            bik="044525226",
        )

    def authenticate(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "supplierapi",
                "password": "StrongTestPassword123!",
            },
            format="json",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )

    def test_supplier_list_requires_authentication(self):
        response = self.client.get(
            reverse("supplier-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_supplier_list_returns_only_current_company_suppliers(self):
        self.authenticate()

        response = self.client.get(
            reverse("supplier-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data["success"],
        )

        self.assertEqual(
            len(response.data["data"]),
            1,
        )

        self.assertEqual(
            response.data["data"][0]["id"],
            self.supplier.id,
        )

        self.assertNotEqual(
            response.data["data"][0]["id"],
            self.other_supplier.id,
        )

    def test_supplier_create_creates_supplier_for_current_company(self):
        self.authenticate()

        response = self.client.post(
            reverse("supplier-list"),
            {
                "legal_name": "Created Supplier",
                "normalized_name": "created supplier",
                "inn": "7707654321",
                "kpp": "770201001",
                "bank_account": "40702810900000000003",
                "bik": "044525227",
                "status": Supplier.Status.ACTIVE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            response.data["success"],
        )

        supplier = Supplier.objects.get(
            inn="7707654321",
        )

        self.assertEqual(
            supplier.company_id,
            self.company.id,
        )
