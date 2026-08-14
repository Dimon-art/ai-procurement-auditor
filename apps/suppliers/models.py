from django.db import models


class Supplier(models.Model):
    """
    Supplier master data for a company.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.PROTECT,
        related_name="suppliers",
    )

    legal_name = models.CharField(
        max_length=255,
    )

    normalized_name = models.CharField(
        max_length=255,
        blank=True,
    )

    inn = models.CharField(
        max_length=12,
    )

    kpp = models.CharField(
        max_length=9,
        blank=True,
    )

    bank_account = models.CharField(
        max_length=20,
        blank=True,
    )

    bik = models.CharField(
        max_length=9,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
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
        return self.legal_name

# Create your models here.
