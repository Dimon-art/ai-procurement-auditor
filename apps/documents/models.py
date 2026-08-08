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

