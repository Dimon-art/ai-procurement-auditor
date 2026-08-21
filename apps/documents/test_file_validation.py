from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework import serializers

from apps.documents.services.file_validation import (
    MAX_FILE_SIZE,
    validate_uploaded_file,
)


class FileValidationTests(SimpleTestCase):
    def test_accepts_valid_pdf(self):
        file = SimpleUploadedFile(
            "invoice.pdf",
            b"%PDF-1.7\nfake pdf content",
            content_type="application/pdf",
        )

        result = validate_uploaded_file(file)

        self.assertIs(result, file)

    def test_accepts_valid_png(self):
        file = SimpleUploadedFile(
            "invoice.png",
            b"\x89PNG\r\n\x1a\nfake png content",
            content_type="image/png",
        )

        result = validate_uploaded_file(file)

        self.assertIs(result, file)

    def test_accepts_valid_jpeg(self):
        file = SimpleUploadedFile(
            "invoice.jpg",
            b"\xff\xd8\xff\xe0fake jpeg content",
            content_type="image/jpeg",
        )

        result = validate_uploaded_file(file)

        self.assertIs(result, file)

    def test_rejects_unsupported_extension(self):
        file = SimpleUploadedFile(
            "virus.exe",
            b"MZfake executable content",
            content_type="application/octet-stream",
        )

        with self.assertRaises(serializers.ValidationError):
            validate_uploaded_file(file)

    def test_rejects_renamed_executable_as_pdf(self):
        file = SimpleUploadedFile(
            "invoice.pdf",
            b"MZfake executable content",
            content_type="application/pdf",
        )

        with self.assertRaises(serializers.ValidationError) as context:
            validate_uploaded_file(file)

        self.assertIn(
            "Содержимое файла не соответствует заявленному формату.",
            str(context.exception),
        )

    def test_rejects_pdf_with_wrong_mime_type(self):
        file = SimpleUploadedFile(
            "invoice.pdf",
            b"%PDF-1.7\nfake pdf content",
            content_type="image/png",
        )

        with self.assertRaises(serializers.ValidationError):
            validate_uploaded_file(file)

    def test_rejects_png_with_wrong_signature(self):
        file = SimpleUploadedFile(
            "invoice.png",
            b"not a real png file",
            content_type="image/png",
        )

        with self.assertRaises(serializers.ValidationError):
            validate_uploaded_file(file)

    def test_rejects_jpeg_with_wrong_signature(self):
        file = SimpleUploadedFile(
            "invoice.jpg",
            b"not a real jpeg file",
            content_type="image/jpeg",
        )

        with self.assertRaises(serializers.ValidationError):
            validate_uploaded_file(file)

    def test_rejects_file_larger_than_15_mb(self):
        file = SimpleUploadedFile(
            "large.pdf",
            b"%PDF-1.7\n" + b"x" * MAX_FILE_SIZE,
            content_type="application/pdf",
        )

        with self.assertRaises(serializers.ValidationError) as context:
            validate_uploaded_file(file)

        self.assertIn(
            "размер файла — до 15 МБ",
            str(context.exception),
        )