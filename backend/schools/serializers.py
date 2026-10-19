from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "role", "school_name")


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
