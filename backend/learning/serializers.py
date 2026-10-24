from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from schools.models import User

from .models import Attempt, Question, Subject, Topic


class SubjectSerializer(serializers.ModelSerializer):
    topic_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subject
        fields = ("id", "name", "slug", "description", "topic_count")


class TopicSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Topic
        fields = (
            "id",
            "subject",
            "title",
            "slug",
            "summary",
            "content",
            "grade",
            "term",
            "question_count",
        )


class QuestionSerializer(serializers.ModelSerializer):
    work_check_available = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            "id",
            "topic",
            "kind",
            "prompt",
            "options",
            "difficulty",
            "work_check_available",
        )

    def get_work_check_available(self, question):
        return bool(settings.GEMINI_API_KEY)


class AttemptSubmissionSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.CharField(allow_blank=False, trim_whitespace=True)


class StudentAccountSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(min_length=8, trim_whitespace=False, write_only=True)
    first_name = serializers.CharField(max_length=150, trim_whitespace=True)
    last_name = serializers.CharField(max_length=150, trim_whitespace=True)
    grade = serializers.ChoiceField(choices=User.Grade.choices)
    class_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        try:
            validate_password(attrs["password"], user=User(username=attrs["username"]))
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from error
        return attrs


class BulkStudentCreateSerializer(serializers.Serializer):
    students = StudentAccountSerializer(many=True, allow_empty=False, max_length=200)

    def validate_students(self, students):
        usernames = [student["username"] for student in students]
        if len(usernames) != len(set(usernames)):
            raise serializers.ValidationError("Usernames must be unique within the batch.")
        return students


class ReportFilterSerializer(serializers.Serializer):
    class_id = serializers.IntegerField(required=False)
    subject_id = serializers.IntegerField(required=False)
    grade = serializers.ChoiceField(required=False, choices=User.Grade.choices)


class SchoolClassSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100, trim_whitespace=True)


class StudentAdminSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="school_class.name", read_only=True, allow_null=True)
    grade_label = serializers.CharField(source="get_grade_display", read_only=True, allow_null=True)
    total_attempts = serializers.IntegerField(read_only=True)
    average_score = serializers.FloatField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "grade",
            "grade_label",
            "class_name",
            "is_active",
            "total_attempts",
            "average_score",
        )


class StudentStatusSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


class StudentPasswordResetSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        try:
            validate_password(attrs["password"], user=self.context["user"])
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from error
        return attrs


class TeacherAccountSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(min_length=8, trim_whitespace=False, write_only=True)
    first_name = serializers.CharField(max_length=150, trim_whitespace=True)
    last_name = serializers.CharField(max_length=150, trim_whitespace=True)

    def validate(self, attrs):
        try:
            validate_password(attrs["password"], user=User(username=attrs["username"]))
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages}) from error
        return attrs


class AttemptResultSerializer(serializers.ModelSerializer):
    question_prompt = serializers.CharField(source="question.prompt", read_only=True)
    subject = serializers.CharField(source="question.topic.subject.name", read_only=True)
    topic = serializers.CharField(source="question.topic.title", read_only=True)
    correct_answer = serializers.CharField(source="question.correct_answer", read_only=True)
    worked_solution = serializers.CharField(source="question.explanation", read_only=True)
    question_kind = serializers.CharField(source="question.kind", read_only=True)
    mark_guide = serializers.CharField(source="question.rubric", read_only=True)

    class Meta:
        model = Attempt
        fields = (
            "id",
            "question",
            "question_prompt",
            "subject",
            "topic",
            "submitted_answer",
            "is_correct",
            "score",
            "feedback",
            "correct_answer",
            "worked_solution",
            "question_kind",
            "mark_guide",
            "created_at",
        )
