from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.companies.models import Company
from apps.users.models import UserProfile
from apps.users.serializers import UserProfileSerializer


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

        self.other_company = Company.objects.create(
            name="Другая компания",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Тестовый пользователь",
            role=UserProfile.Role.ACCOUNTANT,
            status=UserProfile.Status.ACTIVE,
        )

    def authenticate(self):
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

    def test_current_user_profile_requires_authentication(self):
        response = self.client.get(
            reverse("current-user-profile"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_current_user_profile_returns_b2b_profile(self):
        self.authenticate()

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

    def test_current_user_profile_patch_updates_full_name(self):
        self.authenticate()

        response = self.client.patch(
            reverse("current-user-profile"),
            {
                "full_name": "Новое имя пользователя",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"]["full_name"],
            "Новое имя пользователя",
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.full_name,
            "Новое имя пользователя",
        )

    def test_current_user_profile_patch_cannot_change_role(self):
        self.authenticate()

        response = self.client.patch(
            reverse("current-user-profile"),
            {
                "role": UserProfile.Role.COMPANY_ADMIN,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.role,
            UserProfile.Role.ACCOUNTANT,
        )

    def test_current_user_profile_patch_cannot_change_status(self):
        self.authenticate()

        response = self.client.patch(
            reverse("current-user-profile"),
            {
                "status": UserProfile.Status.INACTIVE,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.status,
            UserProfile.Status.ACTIVE,
        )

    def test_current_user_profile_patch_cannot_change_company(self):
        self.authenticate()

        response = self.client.patch(
            reverse("current-user-profile"),
            {
                "company_id": self.other_company.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.profile.refresh_from_db()

        self.assertEqual(
            self.profile.company_id,
            self.company.id,
        )


class UserProfileSerializerSecurityTests(APITestCase):
    def test_full_name_is_writable(self):
        serializer = UserProfileSerializer()

        self.assertFalse(
            serializer.fields["full_name"].read_only,
        )

    def test_role_is_read_only(self):
        serializer = UserProfileSerializer()

        self.assertTrue(
            serializer.fields["role"].read_only,
        )

    def test_status_is_read_only(self):
        serializer = UserProfileSerializer()

        self.assertTrue(
            serializer.fields["status"].read_only,
        )

    def test_company_fields_are_read_only(self):
        serializer = UserProfileSerializer()

        self.assertTrue(
            serializer.fields["company_id"].read_only,
        )
        self.assertTrue(
            serializer.fields["company_name"].read_only,
        )

    def test_email_is_read_only(self):
        serializer = UserProfileSerializer()

        self.assertTrue(
            serializer.fields["email"].read_only,
        )