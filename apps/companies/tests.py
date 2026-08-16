from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import Company
from apps.users.models import UserProfile


class CompanyListAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="companytest",
            password="StrongTestPassword123!",
        )

        self.company = Company.objects.create(
            name="Тестовая компания",
        )

        UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Тестовый пользователь",
            role=UserProfile.Role.COMPANY_ADMIN,
            status=UserProfile.Status.ACTIVE,
        )

    def test_company_list_requires_authentication(self):
        response = self.client.get(
            reverse("company-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_company_list_returns_current_user_company(self):
        token = str(
            RefreshToken.for_user(self.user).access_token,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        response = self.client.get(
            reverse("company-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"],
            [
                {
                    "id": self.company.id,
                    "name": self.company.name,
                }
            ],
        )
        self.assertIsNone(response.data["message"])
        self.assertEqual(
            response.data["errors"],
            [],
        )