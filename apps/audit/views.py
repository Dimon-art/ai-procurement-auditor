from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer


class AuditLogListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.profile.company

        audit_logs = AuditLog.objects.filter(
            company=company,
        ).order_by("-created_at")

        serializer = AuditLogSerializer(
            audit_logs,
            many=True,
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": None,
                "errors": [],
            }
        )


class AuditLogDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        company = request.user.profile.company

        audit_log = AuditLog.objects.filter(
            company=company,
            pk=pk,
        ).first()

        if audit_log is None:
            return Response(
                {
                    "success": False,
                    "data": None,
                    "message": "Audit log not found.",
                    "errors": [],
                },
                status=404,
            )

        serializer = AuditLogSerializer(
            audit_log,
        )

        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": None,
                "errors": [],
            }
        )
