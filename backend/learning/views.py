from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from schools.models import SchoolClass, TermSubscription, User
from schools.permissions import IsSchoolAdmin, IsStudent
from schools.views import has_school_access

from .models import Attempt, Question, Subject, Topic
from .permissions import HasActiveSchoolAccess
from .serializers import (
    AttemptResultSerializer,
    AttemptSubmissionSerializer,
    BulkStudentCreateSerializer,
    QuestionSerializer,
    ReportFilterSerializer,
    SchoolClassSerializer,
    SubjectSerializer,
    TopicSerializer,
)


class SubjectListView(APIView):
    permission_classes = [HasActiveSchoolAccess]

    def get(self, request):
        subjects = Subject.objects.filter(is_published=True).annotate(
            topic_count=Count("topics", filter=Q(topics__is_published=True))
        )
        return Response(SubjectSerializer(subjects, many=True).data)


class SubjectTopicsView(APIView):
    permission_classes = [HasActiveSchoolAccess]

    def get(self, request, subject_id):
        topics = Topic.objects.filter(
            subject_id=subject_id, subject__is_published=True, is_published=True
        ).annotate(question_count=Count("questions", filter=Q(questions__is_published=True)))
        return Response(TopicSerializer(topics, many=True).data)


class TopicQuestionsView(APIView):
    permission_classes = [HasActiveSchoolAccess]

    def get(self, request, topic_id):
        questions = Question.objects.filter(
            topic_id=topic_id,
            topic__is_published=True,
            topic__subject__is_published=True,
            is_published=True,
            kind=Question.Kind.MCQ,
        )
        return Response(QuestionSerializer(questions, many=True).data)


class AttemptView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsStudent]

    def post(self, request):
        serializer = AttemptSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            question = Question.objects.select_related("topic__subject").get(
                id=serializer.validated_data["question_id"],
                kind=Question.Kind.MCQ,
                is_published=True,
                topic__is_published=True,
                topic__subject__is_published=True,
            )
        except Question.DoesNotExist:
            return Response({"detail": "Question not found."}, status=status.HTTP_404_NOT_FOUND)

        answer = serializer.validated_data["answer"]
        if answer not in question.options:
            return Response(
                {"detail": "Choose one of the available options."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        is_correct = answer == question.correct_answer
        attempt = Attempt.objects.create(
            school=request.user.school,
            student=request.user,
            question=question,
            submitted_answer=answer,
            is_correct=is_correct,
            score=100 if is_correct else 0,
            feedback=(
                "Correct! Great work."
                if is_correct
                else question.explanation or "Review the method, then try a similar question."
            ),
        )
        return Response(AttemptResultSerializer(attempt).data, status=status.HTTP_201_CREATED)


class StudentProgressView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsStudent]

    def get(self, request):
        attempts = Attempt.objects.filter(student=request.user, school=request.user.school)
        summary = attempts.aggregate(
            total=Count("id"),
            correct=Count("id", filter=Q(is_correct=True)),
            average_score=Avg("score"),
        )
        recent = attempts.select_related("question__topic__subject")[:30]
        return Response(
            {
                "summary": {
                    "total_attempts": summary["total"] or 0,
                    "correct_attempts": summary["correct"] or 0,
                    "average_score": round(summary["average_score"] or 0, 1),
                },
                "attempts": AttemptResultSerializer(recent, many=True).data,
            }
        )


class BulkStudentCreateView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolAdmin]

    def post(self, request):
        serializer = BulkStudentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        students = serializer.validated_data["students"]
        usernames = [student["username"] for student in students]
        if User.objects.filter(username__in=usernames).exists():
            return Response(
                {"detail": "One or more usernames are already in use."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        class_ids = {
            student["class_id"]
            for student in students
            if student.get("class_id") is not None
        }
        classes = SchoolClass.objects.filter(
            school=request.user.school, id__in=class_ids
        ).in_bulk()
        if class_ids != set(classes):
            return Response(
                {"detail": "Choose a class that belongs to your school."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                active_subscription = (
                    request.user.school.subscriptions.select_for_update()
                    .filter(
                        status=TermSubscription.Status.ACTIVE,
                        starts_at__lte=timezone.now().date(),
                        ends_at__gte=timezone.now().date(),
                    )
                    .order_by("-seat_limit")
                    .first()
                )
                if active_subscription is None:
                    return Response(
                        {"detail": "No current school subscription is available."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                current_student_count = request.user.school.users.filter(
                    role=User.Role.STUDENT
                ).count()
                if current_student_count + len(students) > active_subscription.seat_limit:
                    return Response(
                        {"detail": f"This term has {active_subscription.seat_limit} student seats."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                created = [
                    User(
                        username=entry["username"],
                        first_name=entry.get("first_name", ""),
                        last_name=entry.get("last_name", ""),
                        role=User.Role.STUDENT,
                        school=request.user.school,
                        school_class=classes.get(entry.get("class_id")),
                    )
                    for entry in students
                ]
                for user, entry in zip(created, students):
                    user.set_password(entry["password"])
                User.objects.bulk_create(created)
        except IntegrityError:
            return Response(
                {"detail": "One or more usernames are already in use."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"created": len(created), "usernames": usernames},
            status=status.HTTP_201_CREATED,
        )


class SchoolClassesView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolAdmin]

    def get(self, request):
        classes = SchoolClass.objects.filter(school=request.user.school)
        return Response(SchoolClassSerializer(classes, many=True).data)

    def post(self, request):
        serializer = SchoolClassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        school_class, created = SchoolClass.objects.get_or_create(
            school=request.user.school,
            name=serializer.validated_data["name"],
        )
        if not created:
            return Response(
                {"detail": "That class already exists for your school."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(SchoolClassSerializer(school_class).data, status=status.HTTP_201_CREATED)


class SchoolReportsView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolAdmin]

    def get(self, request):
        filters = ReportFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        class_id = filters.validated_data.get("class_id")
        subject_id = filters.validated_data.get("subject_id")
        school_classes = SchoolClass.objects.filter(school=request.user.school)
        if class_id and not school_classes.filter(id=class_id).exists():
            return Response({"detail": "Class not found."}, status=status.HTTP_404_NOT_FOUND)
        if subject_id and not Subject.objects.filter(id=subject_id, is_published=True).exists():
            return Response({"detail": "Subject not found."}, status=status.HTTP_404_NOT_FOUND)

        attempts = Attempt.objects.filter(school=request.user.school)
        if class_id:
            attempts = attempts.filter(student__school_class_id=class_id)
        if subject_id:
            attempts = attempts.filter(question__topic__subject_id=subject_id)
        report = attempts.aggregate(
            total_attempts=Count("id"),
            correct_attempts=Count("id", filter=Q(is_correct=True)),
            average_score=Avg("score"),
        )
        by_subject = (
            attempts.values("question__topic__subject__id", "question__topic__subject__name")
            .annotate(
                attempts=Count("id"),
                correct=Count("id", filter=Q(is_correct=True)),
                average_score=Avg("score"),
            )
            .order_by("question__topic__subject__name")
        )
        student_query = request.user.school.users.filter(role=User.Role.STUDENT)
        student_attempt_filter = Q(attempts__school=request.user.school)
        if class_id:
            student_query = student_query.filter(school_class_id=class_id)
        if subject_id:
            student_attempt_filter &= Q(attempts__question__topic__subject_id=subject_id)
        students = (
            student_query
            .annotate(
                total_attempts=Count("attempts", filter=student_attempt_filter),
                average_score=Avg("attempts__score", filter=student_attempt_filter),
            )
            .values("id", "username", "first_name", "last_name", "total_attempts", "average_score")
            .order_by("username")
        )
        current_date = timezone.now().date()
        subscription = request.user.school.subscriptions.filter(
            status=TermSubscription.Status.ACTIVE,
            starts_at__lte=current_date,
            ends_at__gte=current_date,
        ).first()
        if subscription is None:
            subscription = request.user.school.subscriptions.order_by("-starts_at").first()
        return Response(
            {
                "school": request.user.school.name,
                "student_count": student_query.count(),
                "total_student_count": request.user.school.users.filter(
                    role=User.Role.STUDENT
                ).count(),
                "classes": SchoolClassSerializer(school_classes, many=True).data,
                "available_subjects": list(
                    Subject.objects.filter(is_published=True)
                    .order_by("position", "name")
                    .values("id", "name")
                ),
                "subscription": (
                    {
                        "term_name": subscription.term_name,
                        "starts_at": subscription.starts_at.isoformat(),
                        "ends_at": subscription.ends_at.isoformat(),
                        "seat_limit": subscription.seat_limit,
                        "status": subscription.status,
                        "is_current": subscription.is_current,
                    }
                    if subscription
                    else None
                ),
                "summary": {
                    "total_attempts": report["total_attempts"] or 0,
                    "correct_attempts": report["correct_attempts"] or 0,
                    "average_score": round(report["average_score"] or 0, 1),
                },
                "subjects": list(by_subject),
                "students": list(students),
            }
        )
