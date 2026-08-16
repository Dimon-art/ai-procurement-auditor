from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class Role(models.TextChoices):
        OPERATOR = "operator", "Operator"
        ACCOUNTANT = "accountant", "Accountant"
        MANAGER = "manager", "Manager"
        COMPANY_ADMIN = "company_admin", "Company admin"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.PROTECT,
        related_name="user_profiles",
    )

    full_name = models.CharField(
        max_length=255,
    )

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.OPERATOR,
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return self.full_name