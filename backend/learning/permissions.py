from rest_framework.permissions import BasePermission

from schools.views import has_school_access


class HasActiveSchoolAccess(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and has_school_access(request.user))
