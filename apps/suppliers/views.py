from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.suppliers.models import Supplier
from apps.suppliers.serializers import SupplierSerializer


class SupplierListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.profile.company

        suppliers = Supplier.objects.filter(
            company=company,
        ).order_by("legal_name")

        serializer = SupplierSerializer(
            suppliers,
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

    def post(self, request):
        serializer = SupplierSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        supplier = serializer.save(
            company=request.user.profile.company,
        )

        return Response(
            {
                "success": True,
                "data": SupplierSerializer(supplier).data,
                "message": None,
                "errors": [],
            },
            status=201,
        )