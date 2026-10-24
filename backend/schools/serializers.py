from rest_framework import serializers

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True, allow_null=True)
    school_code = serializers.CharField(source="school.slug", read_only=True, allow_null=True)
    grade_label = serializers.CharField(source="get_grade_display", read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "role",
            "school_name",
            "school_code",
            "grade",
            "grade_label",
        )


class LoginSerializer(serializers.Serializer):
    school_code = serializers.CharField(
        required=False, allow_blank=True, trim_whitespace=True, max_length=100
    )
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(
        write_only=True, trim_whitespace=False, max_length=256
    )


class SchoolRegistrationSerializer(serializers.Serializer):
    school_name = serializers.CharField(max_length=200, trim_whitespace=True)
    first_name = serializers.CharField(max_length=150, trim_whitespace=True)
    last_name = serializers.CharField(max_length=150, trim_whitespace=True)
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(min_length=8, trim_whitespace=False, write_only=True)

    def validate_password(self, password):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        try:
            validate_password(
                password,
                user=User(
                    username=self.initial_data.get("username", ""),
                    first_name=self.initial_data.get("first_name", ""),
                    last_name=self.initial_data.get("last_name", ""),
                ),
            )
        except ValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return password


class StudentRegistrationSerializer(serializers.Serializer):
    school_code = serializers.CharField(max_length=100, trim_whitespace=True)
    first_name = serializers.CharField(max_length=150, trim_whitespace=True)
    last_name = serializers.CharField(max_length=150, trim_whitespace=True)
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(min_length=8, trim_whitespace=False, write_only=True)
    grade = serializers.ChoiceField(choices=User.Grade.choices)

    def validate_password(self, password):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        try:
            validate_password(
                password,
                user=User(
                    username=self.initial_data.get("username", ""),
                    first_name=self.initial_data.get("first_name", ""),
                    last_name=self.initial_data.get("last_name", ""),
                ),
            )
        except ValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return password
