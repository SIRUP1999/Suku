from rest_framework.permissions import BasePermission

from .models import User


class IsSchoolAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.SCHOOL_ADMIN
            and request.user.school_id
        )


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.STUDENT
            and request.user.school_id
        )
