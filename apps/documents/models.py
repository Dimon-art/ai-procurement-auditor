from django.db import models


class Document(models.Model):
    """
    Загруженный пользователем документ.
    """

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        OCR = "ocr", "OCR completed"
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


