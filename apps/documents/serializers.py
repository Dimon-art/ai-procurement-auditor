from rest_framework import serializers

from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(
        source="company.id",
        read_only=True,
    )

    class Meta:
        model = Document
        fields = (
            "id",
            "company_id",
            "filename",
            "file_hash",
            "file_size",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "company_id",
            "filename",
            "file_hash",
            "file_size",
            "status",
            "created_at",
            "updated_at",
        )

class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = (
            "original_file",
        )        