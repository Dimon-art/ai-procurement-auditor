from rest_framework import serializers

from apps.documents.models import OCRResult


class PipelineHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRResult
        fields = (
            "id",
            "provider",
            "confidence",
            "processing_time_ms",
            "error_message",
            "created_at",
        )
        read_only_fields = fields