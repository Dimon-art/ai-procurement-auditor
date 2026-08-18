from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit trail entry for company business events.
    """

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.PROTECT,
        related_name="audit_logs",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_logs",
        null=True,
        blank=True,
    )

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.PROTECT,
        related_name="audit_logs",
        null=True,
        blank=True,
    )

    action = models.CharField(
        max_length=64,
    )

    entity_type = models.CharField(
        max_length=64,
    )

    entity_id = models.CharField(
        max_length=64,
        blank=True,
    )

    previous_value = models.JSONField(
        null=True,
        blank=True,
    )

    new_value = models.JSONField(
        null=True,
        blank=True,
    )

    metadata = models.JSONField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.action} "
            f"{self.entity_type} "
            f"{self.entity_id}"
        )
