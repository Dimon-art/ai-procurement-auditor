from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.forms import RegistrationForm
from apps.users.serializers import UserProfileSerializer


class RegisterView(View):
    template_name = "registration/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("document-list-page")

        return render(
            request,
            self.template_name,
            {
                "form": RegistrationForm(),
            },
        )

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("document-list-page")

        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("document-list-page")

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )


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
