from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.audit.models import AuditLog
from apps.companies.models import Company
from apps.documents.models import Document
from apps.users.models import UserProfile


class AuditLogModelTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Audit Model Company",
        )

    def test_audit_log_is_linked_to_company(self):
        audit_log = AuditLog.objects.create(
            company=self.company,
            action="document.recheck",
            entity_type="document",
            entity_id="1",
            metadata={
                "source": "test",
            },
        )

        self.assertEqual(
            audit_log.company,
            self.company,
        )

        self.assertEqual(
            audit_log.action,
            "document.recheck",
        )


class AuditLogAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="auditapi",
            password="StrongTestPassword123!",
        )

        self.company = Company.objects.create(
            name="Audit API Company",
        )

        self.other_company = Company.objects.create(
            name="Other Audit Company",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            company=self.company,
            full_name="Audit API User",
            role=UserProfile.Role.ACCOUNTANT,
            status=UserProfile.Status.ACTIVE,
        )

        self.document = Document.objects.create(
            company=self.company,
            filename="audit_invoice.pdf",
            file_size=1,
        )

        self.audit_log = AuditLog.objects.create(
            company=self.company,
            user=self.user,
            document=self.document,
            action="document.recheck",
            entity_type="document",
            entity_id=str(self.document.pk),
            metadata={
                "source": "api-test",
            },
        )

        self.other_audit_log = AuditLog.objects.create(
            company=self.other_company,
            action="document.recheck",
            entity_type="document",
            entity_id="999",
        )

    def authenticate(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "auditapi",
                "password": "StrongTestPassword123!",
            },
            format="json",
        )

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )

    def test_audit_list_requires_authentication(self):
        response = self.client.get(
            reverse("audit-log-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_audit_list_returns_only_current_company_logs(self):
        self.authenticate()

        response = self.client.get(
            reverse("audit-log-list"),
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
            self.audit_log.id,
        )

    def test_audit_detail_returns_current_company_log(self):
        self.authenticate()

        response = self.client.get(
            reverse(
                "audit-log-detail",
                kwargs={"pk": self.audit_log.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            response.data["success"],
        )

        self.assertEqual(
            response.data["data"]["id"],
            self.audit_log.id,
        )

    def test_audit_detail_does_not_return_other_company_log(self):
        self.authenticate()

        response = self.client.get(
            reverse(
                "audit-log-detail",
                kwargs={"pk": self.other_audit_log.pk},
            ),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertFalse(
            response.data["success"],
        )

        self.assertIsNone(
            response.data["data"],
        )