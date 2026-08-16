from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.companies.serializers import CompanySerializer


class CompanyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company = request.user.profile.company
        serializer = CompanySerializer(company)

        return Response(
            {
                "success": True,
                "data": [serializer.data],
                "message": None,
                "errors": [],
            }
        )

