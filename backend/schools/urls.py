from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CurrentUserView,
    LoginView,
    SchoolRegistrationView,
    StudentRegistrationView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("auth/register-school/", SchoolRegistrationView.as_view(), name="register-school"),
    path("auth/register-student/", StudentRegistrationView.as_view(), name="register-student"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
