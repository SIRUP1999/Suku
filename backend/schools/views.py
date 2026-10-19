from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import LoginSerializer, UserProfileSerializer
from .throttles import LoginIPThrottle, LoginUsernameThrottle


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
    throttle_classes = [LoginIPThrottle, LoginUsernameThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school_code = serializer.validated_data.get("school_code", "").strip()
        username = serializer.validated_data["username"].strip()
        password = serializer.validated_data["password"]
        user = authenticate(
            request,
            username=username,
            password=password,
            school_code=school_code or None,
        )
        if not user or (not school_code and not user.is_superuser):
            return Response({"detail": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_superuser and user.role not in (
            User.Role.SCHOOL_ADMIN,
            User.Role.STUDENT,
        ):
            return Response(
                {"detail": "This account role is not enabled in the current version."},
                status=status.HTTP_403_FORBIDDEN,
            )
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
