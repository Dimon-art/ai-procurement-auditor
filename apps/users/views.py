from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers import UserProfileSerializer


class CurrentUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)

        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": None,
                "errors": [],
            }
        )

    def patch(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": None,
                "errors": [],
            }
        )