from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import LoginSerializer, UserProfileSerializer


def has_school_access(user):
    return bool(
        user.is_active
        and user.school_id
        and user.school.status == user.school.Status.ACTIVE
        and user.school.has_current_subscription
    )


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_superuser and not has_school_access(user):
            return Response(
                {"detail": "Your school's access is not active. Please contact your school administrator."},
                status=status.HTTP_403_FORBIDDEN,
            )
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserProfileSerializer(user).data,
            }
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser and not has_school_access(request.user):
            return Response({"detail": "School access is inactive."}, status=status.HTTP_403_FORBIDDEN)
        return Response(UserProfileSerializer(request.user).data)
