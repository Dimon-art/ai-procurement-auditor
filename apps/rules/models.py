from django.db import models


class CheckResult(models.Model):
    class Status(models.TextChoices):
        PASSED = "passed", "Passed"
        WARNING = "warning", "Warning"
        FAILED = "failed", "Failed"
        NOT_APPLICABLE = "not_applicable", "Not applicable"
        INSUFFICIENT_DATA = "insufficient_data", "Insufficient data"

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="check_results",
    )

    rule_id = models.CharField(
        max_length=32,
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
    )

    severity = models.CharField(
        max_length=16,
    )

    score = models.IntegerField(
        default=0,
    )

    actual_value = models.JSONField(
        null=True,
        blank=True,
    )

    expected_value = models.JSONField(
        null=True,
        blank=True,
    )

    explanation = models.TextField(
        blank=True,
    )

    evidence = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"{self.rule_id} "
            f"for document #{self.document_id}"
        )


