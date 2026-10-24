import json
import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import User


class PlatformAdminSetupTests(TestCase):
    def setUp(self):
        self.token = "one-time-test-token"
        self.environment = patch.dict(
            os.environ,
            {
                "PLATFORM_ADMIN_SETUP_TOKEN": self.token,
                "PLATFORM_ADMIN_SETUP_EXPIRES_AT": (
                    timezone.now() + timedelta(hours=1)
                ).isoformat(),
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_creates_one_platform_superuser(self):
        response = self.client.post(
            reverse("platform-admin-setup"),
            data=json.dumps({"password": "Strong-random-password-892!"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, 201)
        admin_user = User.objects.get(username="albertofori")
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.check_password("Strong-random-password-892!"))

        login_response = self.client.post(
            reverse("login"),
            data={
                "username": "albertofori",
                "password": "Strong-random-password-892!",
            },
        )
        self.assertEqual(login_response.status_code, 200)

        repeated = self.client.post(
            reverse("platform-admin-setup"),
            data=json.dumps({"password": "Another-strong-password-832!"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(repeated.status_code, 409)
        admin_user.refresh_from_db()
        self.assertTrue(admin_user.check_password("Strong-random-password-892!"))

    def test_rejects_invalid_setup_token(self):
        response = self.client.post(
            reverse("platform-admin-setup"),
            data=json.dumps({"password": "Strong-random-password-892!"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer wrong-token",
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(User.objects.filter(is_superuser=True).exists())

    def test_rejects_short_password(self):
        response = self.client.post(
            reverse("platform-admin-setup"),
            data=json.dumps({"password": "short"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(is_superuser=True).exists())
