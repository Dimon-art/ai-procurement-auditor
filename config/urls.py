from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.documents.views import upload_document
from apps.users.views import CurrentUserProfileView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("documents/upload/", upload_document, name="document-upload"),
    path(
        "api/v1/auth/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/v1/auth/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/v1/users/me/",
        CurrentUserProfileView.as_view(),
        name="current-user-profile",
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )