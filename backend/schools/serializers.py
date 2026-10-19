from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True, allow_null=True)
    school_code = serializers.CharField(source="school.slug", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "role", "school_name", "school_code")


class LoginSerializer(serializers.Serializer):
    school_code = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True, max_length=100
    )
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=256
    )
