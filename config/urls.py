from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from apps.audit.views import AuditLogDetailView, AuditLogListView
from apps.companies.views import CompanyListView
from apps.documents.views import (
    DocumentApprovePageView,
    DocumentDetailPageView,
    DocumentDetailView,
    DocumentListPageView,
    DocumentListView,
    DocumentRecheckView,
    DocumentReportView,
    DocumentStatusView,
    PipelineHistoryView,
    PipelineRestartView,
    PipelineStartView,
    PipelineStatusView,
    upload_document,
)
from apps.suppliers.views import SupplierListView
from apps.users.views import CurrentUserProfileView
from config.health import health_check


urlpatterns = [
    path("", DocumentListPageView.as_view()),
    path(
        "health/",
        health_check,
        name="health-check",
    ),
    path(
        "admin/",
        admin.site.urls,
    ),
    path(
        "login/",
        LoginView.as_view(
            template_name="registration/login.html",
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "documents/",
        DocumentListPageView.as_view(),
        name="document-list-page",
    ),
    path(
        "documents/upload/",
        upload_document,
        name="document-upload",
    ),
    path(
        "documents/<int:pk>/approve/",
        DocumentApprovePageView.as_view(),
        name="document-approve-page",
    ),
    path(
        "documents/<int:pk>/",
        DocumentDetailPageView.as_view(),
        name="document-detail-page",
    ),
    path(
        "api/v1/auth/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/v1/companies/",
        CompanyListView.as_view(),
        name="company-list",
    ),
    path(
        "api/v1/suppliers/",
        SupplierListView.as_view(),
        name="supplier-list",
    ),
    path(
        "api/v1/documents/",
        DocumentListView.as_view(),
        name="document-list",
    ),
    path(
        "api/v1/documents/<int:pk>/",
        DocumentDetailView.as_view(),
        name="document-detail",
    ),
    path(
        "api/v1/documents/<int:pk>/status/",
        DocumentStatusView.as_view(),
        name="document-status",
    ),
    path(
        "api/v1/documents/<int:pk>/recheck/",
        DocumentRecheckView.as_view(),
        name="document-recheck",
    ),
    path(
        "api/v1/documents/<int:pk>/report/",
        DocumentReportView.as_view(),
        name="document-report",
    ),
    path(
        "api/v1/reports/<int:pk>/",
        DocumentReportView.as_view(),
        name="report-detail",
    ),
    path(
        "api/v1/pipeline/<int:document_id>/start/",
        PipelineStartView.as_view(),
        name="pipeline-start",
    ),
    path(
        "api/v1/pipeline/<int:document_id>/status/",
        PipelineStatusView.as_view(),
        name="pipeline-status",
    ),
    path(
        "api/v1/pipeline/<int:document_id>/history/",
        PipelineHistoryView.as_view(),
        name="pipeline-history",
    ),
    path(
        "api/v1/pipeline/<int:document_id>/restart/",
        PipelineRestartView.as_view(),
        name="pipeline-restart",
    ),
    path(
        "api/v1/audit/",
        AuditLogListView.as_view(),
        name="audit-log-list",
    ),
    path(
        "api/v1/audit/<int:pk>/",
        AuditLogDetailView.as_view(),
        name="audit-log-detail",
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

