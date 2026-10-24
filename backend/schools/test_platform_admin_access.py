from django.test import TestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APIClient

from .models import User


class PlatformAdminAccessTests(TestCase):
    def test_platform_admin_can_login_and_view_published_subjects(self):
        admin_user = User.objects.create_superuser(
            username="platform-admin",
            password="Strong-random-password-892!",
            role=User.Role.SCHOOL_ADMIN,
        )
        login_response = self.client.post(
            reverse("login"),
            data={
                "username": "platform-admin",
                "password": "Strong-random-password-892!",
            },
        )
        self.assertEqual(login_response.status_code, 200)

        api_client = APIClient()
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(admin_user)}"
        )
        subjects_response = api_client.get(reverse("subject-list"))
        self.assertEqual(subjects_response.status_code, 200)
