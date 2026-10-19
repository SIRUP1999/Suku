from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import CurrentUserView, LoginView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/me/", CurrentUserView.as_view(), name="current-user"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
