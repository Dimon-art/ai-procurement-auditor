from rest_framework import serializers

from apps.suppliers.models import Supplier


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = (
            "id",
            "legal_name",
            "normalized_name",
            "inn",
            "kpp",
            "bank_account",
            "bik",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )