from django.conf import settings
from django.db import models


class Document(models.Model):
    """
    Загруженный пользователем документ.
    """

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        OCR_PROCESSING = "ocr_processing", "OCR processing"
        OCR_COMPLETED = "ocr_completed", "OCR completed"
        VERIFIED = "verified", "Verified"
        ERROR = "error", "Error"

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.PROTECT,
        related_name="documents",
    )

    original_file = models.FileField(
        upload_to="documents/%Y/%m/%d/"
    )

    filename = models.CharField(
        max_length=255
    )

    file_hash = models.CharField(
        max_length=64,
        blank=True,
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.filename


class OCRResult(models.Model):
    """
    Результат одной попытки OCR-распознавания документа.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="ocr_results",
    )

    provider = models.CharField(
        max_length=50,
    )

    raw_text = models.TextField(
        blank=True,
    )

    raw_response = models.JSONField(
        default=dict,
        blank=True,
    )

    confidence = models.FloatField(
        null=True,
        blank=True,
    )

    processing_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"OCR #{self.pk} for {self.document}"


class DocumentField(models.Model):
    """
    Извлеченное структурированное поле документа.
    """

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="fields",
    )

    field_name = models.CharField(
        max_length=64,
    )

    raw_value = models.TextField(
        blank=True,
    )

    normalized_value = models.TextField(
        blank=True,
    )

    corrected_value = models.TextField(
        blank=True,
    )

    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
    )

    source_page = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    bounding_box = models.JSONField(
        null=True,
        blank=True,
    )

    extraction_method = models.CharField(
        max_length=32,
    )

    is_manually_corrected = models.BooleanField(
        default=False,
    )

    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrected_document_fields",
    )

    corrected_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "document",
                    "field_name",
                ],
                name="unique_document_field",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(confidence__isnull=True)
                    | (
                        models.Q(confidence__gte=0)
                        & models.Q(confidence__lte=1)
                    )
                ),
                name="document_field_confidence_0_1",
            ),
        ]

    def __str__(self):
        return (
            f"{self.field_name} "
            f"for document #{self.document_id}"
        )