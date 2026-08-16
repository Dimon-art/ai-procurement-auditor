from rest_framework import serializers

from apps.users.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    company_id = serializers.IntegerField(
        source="company.id",
        read_only=True,
    )

    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
    )

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "email",
            "full_name",
            "role",
            "status",
            "company_id",
            "company_name",
        )
        read_only_fields = (
            "id",
            "email",
            "company_id",
            "company_name",
        )