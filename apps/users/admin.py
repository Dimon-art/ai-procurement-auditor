from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.users.models import UserProfile


User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    fk_name = "user"
    extra = 0
    min_num = 1
    fields = (
        "company",
        "full_name",
        "role",
        "status",
    )


class UserAdmin(DjangoUserAdmin):
    inlines = (UserProfileInline,)
    list_display = (
        "username",
        "email",
        "is_staff",
        "is_active",
        "get_role",
        "get_company",
        "get_profile_status",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "profile__role",
        "profile__status",
        "profile__company",
    )
    search_fields = (
        "username",
        "email",
        "profile__full_name",
        "profile__company__name",
    )

    @admin.display(description="Роль")
    def get_role(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.get_role_display() if profile else "—"

    @admin.display(description="Компания")
    def get_company(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.company if profile else "—"

    @admin.display(description="Статус профиля")
    def get_profile_status(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.get_status_display() if profile else "—"


# Replace default auth.UserAdmin to avoid AlreadyRegistered.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


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

    list_editable = (
        "role",
        "status",
        "company",
    )
