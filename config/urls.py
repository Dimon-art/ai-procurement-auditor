from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from apps.documents.views import upload_document


urlpatterns = [
    path("admin/", admin.site.urls),
    path("documents/upload/", upload_document, name="document-upload"),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )