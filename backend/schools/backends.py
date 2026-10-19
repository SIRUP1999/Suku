from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import MultipleObjectsReturned

from .models import School, User


class SchoolAwareModelBackend(ModelBackend):
    def authenticate(
        self,
        request,
        username=None,
        password=None,
        school_code=None,
        **kwargs,
    ):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        if school_code:
            school = School.objects.filter(slug__iexact=school_code).first()
            user = (
                User.objects.filter(
                    school=school,
                    username__iexact=username,
                    is_active=True,
                ).first()
                if school
                else None
            )
            return user if user and user.check_password(password) else None

        try:
            return super().authenticate(request, username=username, password=password, **kwargs)
        except MultipleObjectsReturned:
            return None
