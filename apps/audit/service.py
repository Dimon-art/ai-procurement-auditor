from typing import Any

from django.contrib.auth import get_user_model

from apps.audit.models import AuditLog
from apps.companies.models import Company
from apps.documents.models import Document


def create_audit_log(
    *,
    company: Company,
    action: str,
    entity_type: str,
    user=None,
    document: Document | None = None,
    entity_id: str = "",
    previous_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Create an immutable audit log entry for a business event.
    """

    return AuditLog.objects.create(
        company=company,
        user=user,
        document=document,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_value=previous_value,
        new_value=new_value,
        metadata=metadata,
    )