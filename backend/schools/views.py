from django.contrib.auth import authenticate
from django.db import IntegrityError, transaction
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import School, TermSubscription, User
from .serializers import (
    LoginSerializer,
    SchoolRegistrationSerializer,
    StudentRegistrationSerializer,
    UserProfileSerializer,
)
from .throttles import LoginIPThrottle, LoginUsernameThrottle, SignupIPThrottle


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
            User.Role.TEACHER,
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


class SchoolRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [SignupIPThrottle]

    def post(self, request):
        serializer = SchoolRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        base_slug = slugify(data["school_name"])[:45].strip("-") or "school"

        try:
            with transaction.atomic():
                slug = base_slug
                suffix = 2
                while School.objects.filter(slug__iexact=slug).exists():
                    slug = f"{base_slug[:45 - len(str(suffix))]}-{suffix}"
                    suffix += 1
                school = School.objects.create(name=data["school_name"], slug=slug)
                User.objects.create_user(
                    username=data["username"],
                    password=data["password"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    role=User.Role.SCHOOL_ADMIN,
                    school=school,
                )
        except IntegrityError:
            return Response(
                {"detail": "Could not register this school account. Please try a different username."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "School registration received. Access will be available after school approval and subscription setup.",
                "school_name": school.name,
                "school_code": school.slug,
            },
            status=status.HTTP_201_CREATED,
        )


class StudentRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [SignupIPThrottle]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            school = (
                School.objects.select_for_update()
                .filter(slug__iexact=data["school_code"])
                .first()
            )
            if school is None or not school.has_current_subscription or school.status != School.Status.ACTIVE:
                return Response(
                    {"detail": "This school code is not accepting sign-ups. Check the code or contact your school administrator."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if User.objects.filter(school=school).annotate(
                normalized_username=Lower("username")
            ).filter(normalized_username=data["username"].lower()).exists():
                return Response(
                    {"username": "That username is already used at this school. Choose another."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            active_subscription = (
                school.subscriptions.select_for_update()
                .filter(
                    status=TermSubscription.Status.ACTIVE,
                    starts_at__lte=timezone.now().date(),
                    ends_at__gte=timezone.now().date(),
                )
                .order_by("-seat_limit")
                .first()
            )
            if active_subscription is None:
                return Response(
                    {"detail": "This school does not have an active subscription."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            active_count = school.users.filter(
                role=User.Role.STUDENT, is_active=True
            ).count()
            if active_count >= active_subscription.seat_limit:
                return Response(
                    {"detail": "All student places for this school are currently in use. Please contact your school administrator."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            try:
                with transaction.atomic():
                    student = User.objects.create_user(
                        username=data["username"],
                        password=data["password"],
                        first_name=data["first_name"],
                        last_name=data["last_name"],
                        role=User.Role.STUDENT,
                        school=school,
                        grade=int(data["grade"]),
                    )
            except IntegrityError:
                return Response(
                    {"username": "That username is already used at this school. Choose another."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        refresh = RefreshToken.for_user(student)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserProfileSerializer(student).data,
            },
            status=status.HTTP_201_CREATED,
        )
