from django.contrib import admin

from apps.users.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "full_name",
        "role",
        "status",
        "created_at",
    )

    list_filter = (
        "company",
        "role",
        "status",
    )

    search_fields = (
        "user__username",
        "user__email",
        "full_name",
        "company__name",
    )