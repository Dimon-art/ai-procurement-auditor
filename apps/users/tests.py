from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.companies.models import Company
from apps.users.models import UserProfile


class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = "testuser"
        self.password = "StrongTestPassword123!"

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username=self.username,
            password=self.password,
        )

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_refresh_returns_new_access_token(self):
        login_response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )

        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            reverse("token_refresh"),
            {
                "refresh": refresh_token,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("access", response.data)


class CurrentUserProfileAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = "profiletest"
        self.password = "StrongTestPassword123!"

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username=self.username,
            email="profiletest@example.com",
            password=self.password,
        )

        self.company = Company.objects.create(
            name="Тестовая компания",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Тестовый пользователь",
            role=UserProfile.Role.ACCOUNTANT,
            status=UserProfile.Status.ACTIVE,
        )

    def test_current_user_profile_requires_authentication(self):
        response = self.client.get(
            reverse("current-user-profile"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_current_user_profile_returns_b2b_profile(self):
        login_response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": self.username,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(
            login_response.status_code,
            status.HTTP_200_OK,
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}",
        )

        response = self.client.get(
            reverse("current-user-profile"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(response.data["success"])
        self.assertIsNone(response.data["message"])
        self.assertEqual(response.data["errors"], [])

        self.assertEqual(
            response.data["data"],
            {
                "id": self.profile.id,
                "email": self.user.email,
                "full_name": "Тестовый пользователь",
                "role": "accountant",
                "status": "active",
                "company_id": self.company.id,
                "company_name": "Тестовая компания",
            },
        )

