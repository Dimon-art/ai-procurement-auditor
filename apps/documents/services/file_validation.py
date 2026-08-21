from pathlib import Path

from rest_framework import serializers


MAX_FILE_SIZE = 15 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
}

ALLOWED_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def validate_uploaded_file(uploaded_file):
    """
    Validate uploaded document before saving it.

    Checks:
    - file size;
    - file extension;
    - declared MIME type;
    - actual file signature.
    """

    filename = uploaded_file.name or ""
    extension = Path(filename).suffix.lower()

    if uploaded_file.size > MAX_FILE_SIZE:
        raise serializers.ValidationError(
            "Разрешены PDF, PNG, JPG; "
            "размер файла — до 15 МБ."
        )

    if extension not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            "Разрешены только PDF, PNG и JPG."
        )

    expected_mime_type = ALLOWED_MIME_TYPES[extension]

    if uploaded_file.content_type != expected_mime_type:
        raise serializers.ValidationError(
            "Содержимое файла не соответствует заявленному формату."
        )

    uploaded_file.seek(0)
    header = uploaded_file.read(16)
    uploaded_file.seek(0)

    if not _has_valid_signature(
        extension,
        header,
    ):
        raise serializers.ValidationError(
            "Содержимое файла не соответствует заявленному формату."
        )

    return uploaded_file


def _has_valid_signature(
    extension: str,
    header: bytes,
) -> bool:
    if extension == ".pdf":
        return header.startswith(b"%PDF-")

    if extension == ".png":
        return header.startswith(
            b"\x89PNG\r\n\x1a\n"
        )

    if extension in {".jpg", ".jpeg"}:
        return header.startswith(b"\xff\xd8\xff")

    return False