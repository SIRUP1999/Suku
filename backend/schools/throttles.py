import hashlib

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class LoginIPThrottle(AnonRateThrottle):
    scope = "login_ip"


class LoginUsernameThrottle(SimpleRateThrottle):
    scope = "login_username"

    def get_cache_key(self, request, view):
        data = request.data if isinstance(request.data, dict) else {}
        school_code = str(data.get("school_code", "")).strip().lower()
        username = str(data.get("username", "")).strip().lower()
        identity = hashlib.sha256(f"{school_code}:{username}".encode()).hexdigest()
        return self.cache_format % {"scope": self.scope, "ident": identity}
