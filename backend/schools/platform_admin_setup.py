import hmac
import json
import logging
import os
from datetime import datetime

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import User

logger = logging.getLogger(__name__)
ADMIN_USERNAME = "albertofori"


@csrf_exempt
@require_POST
def create_platform_admin(request: HttpRequest) -> JsonResponse:
    token = os.environ.get("PLATFORM_ADMIN_SETUP_TOKEN", "")
    expires_at = os.environ.get("PLATFORM_ADMIN_SETUP_EXPIRES_AT", "")
    if not token or not expires_at:
        return JsonResponse({"detail": "Not found."}, status=404)

    try:
        expiry = datetime.fromisoformat(expires_at)
    except ValueError:
        logger.error("Platform administrator setup expiry is invalid.")
        return JsonResponse({"detail": "Setup is unavailable."}, status=503)
    if timezone.is_naive(expiry):
        logger.error("Platform administrator setup expiry must include a timezone.")
        return JsonResponse({"detail": "Setup is unavailable."}, status=503)
    if timezone.now() >= expiry:
        return JsonResponse({"detail": "This setup link has expired."}, status=410)
    if not hmac.compare_digest(
        request.headers.get("Authorization", ""),
        f"Bearer {token}",
    ):
        return JsonResponse({"detail": "Unauthorized."}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "Send valid JSON."}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"detail": "Send a JSON object."}, status=400)
    password = data.get("password")
    if not isinstance(password, str) or len(password) < 12 or len(password) > 256:
        return JsonResponse(
            {"detail": "Choose a password between 12 and 256 characters."},
            status=400,
        )

    user = User(
        username=ADMIN_USERNAME,
        first_name="Albert",
        last_name="Ofori",
        role=User.Role.SCHOOL_ADMIN,
    )
    try:
        validate_password(password, user=user)
    except ValidationError as error:
        return JsonResponse({"detail": error.messages}, status=400)

    try:
        with transaction.atomic():
            if User.objects.filter(is_superuser=True).exists():
                return JsonResponse(
                    {"detail": "A platform administrator is already configured."},
                    status=409,
                )
            User.objects.create_superuser(
                username=ADMIN_USERNAME,
                password=password,
                first_name="Albert",
                last_name="Ofori",
                role=User.Role.SCHOOL_ADMIN,
            )
    except IntegrityError:
        return JsonResponse(
            {"detail": "This administrator username is already in use."},
            status=409,
        )

    return JsonResponse(
        {"detail": "Platform administrator account created."},
        status=201,
    )
