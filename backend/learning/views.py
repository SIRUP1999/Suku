import csv
import io

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, F, Q
from django.db.models.functions import Lower
from django.utils import timezone
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from schools.models import SchoolClass, TermSubscription, User
from schools.permissions import IsSchoolAdmin, IsSchoolStaff, IsStudent
from schools.views import has_school_access

from .ai import GeminiWorkCheckError, check_written_work
from .models import Attempt, Question, Subject, Topic
from .permissions import HasActiveSchoolAccess
from .serializers import (
    AttemptResultSerializer,
    AttemptSubmissionSerializer,
    BulkStudentCreateSerializer,
    QuestionSerializer,
    ReportFilterSerializer,
    SchoolClassSerializer,
    StudentAdminSerializer,
    StudentPasswordResetSerializer,
    StudentStatusSerializer,
    SubjectSerializer,
    TeacherAccountSerializer,
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
        grade = request.query_params.get("grade")
        topics = Topic.objects.filter(
            subject_id=subject_id, subject__is_published=True, is_published=True
        )
        if grade:
            valid_grades = {str(value) for value, _ in Topic.Grade.choices}
            if grade not in valid_grades:
                return Response(
                    {"grade": "Choose Grade 7, 8, or 9."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            topics = topics.filter(grade=int(grade))
        topics = topics.annotate(
            question_count=Count("questions", filter=Q(questions__is_published=True))
        )
        return Response(TopicSerializer(topics, many=True).data)


class TopicDetailView(APIView):
    permission_classes = [HasActiveSchoolAccess]

    def get(self, request, topic_id):
        try:
            topic = Topic.objects.annotate(
                question_count=Count(
                    "questions",
                    filter=Q(questions__is_published=True),
                )
            ).get(
                id=topic_id,
                is_published=True,
                subject__is_published=True,
            )
        except Topic.DoesNotExist:
            return Response({"detail": "Topic not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TopicSerializer(topic).data)


class TopicQuestionsView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsStudent]

    def get(self, request, topic_id):
        questions = Question.objects.filter(
            topic_id=topic_id,
            topic__is_published=True,
            topic__subject__is_published=True,
            is_published=True,
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
                is_published=True,
                topic__is_published=True,
                topic__subject__is_published=True,
            )
        except Question.DoesNotExist:
            return Response({"detail": "Question not found."}, status=status.HTTP_404_NOT_FOUND)

        answer = serializer.validated_data["answer"]
        is_free_response = question.kind == Question.Kind.THEORY and not question.options
        if is_free_response and not answer.strip():
            return Response(
                {"answer": "Write your working before submitting."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not is_free_response and answer not in question.options:
            return Response(
                {"detail": "Choose one of the available options."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        is_correct = None if is_free_response else answer == question.correct_answer
        attempt = Attempt.objects.create(
            school=request.user.school,
            student=request.user,
            question=question,
            submitted_answer=answer,
            is_correct=is_correct,
            score=None if is_free_response else 100 if is_correct else 0,
            feedback=(
                "Your written response is saved. It is not marked automatically; compare your working with the step-by-step solution and mark guide."
                if is_free_response
                else "Correct! Great work."
                if is_correct
                else "Not quite. Review the worked solution and try the method again."
            ),
        )
        return Response(AttemptResultSerializer(attempt).data, status=status.HTTP_201_CREATED)


class WorkCheckView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsStudent]
    parser_classes = [MultiPartParser, FormParser]
    throttle_scope = "work_check"
    maximum_pdf_bytes = 10 * 1024 * 1024

    def post(self, request, attempt_id):
        if not settings.GEMINI_API_KEY:
            return Response(
                {
                    "detail": (
                        "PDF work checking is not configured yet. "
                        "Please ask your school administrator."
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            attempt = Attempt.objects.select_related("question").get(
                id=attempt_id,
                student=request.user,
                school=request.user.school,
                question__kind=Question.Kind.THEORY,
            )
        except Attempt.DoesNotExist:
            return Response(
                {"detail": "Theory attempt not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        uploaded = request.FILES.get("work")
        if uploaded is None:
            return Response(
                {"work": "Upload a PDF of your written work."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if uploaded.size > self.maximum_pdf_bytes:
            return Response(
                {"work": "PDF files must be 10 MB or smaller."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not uploaded.name.lower().endswith(".pdf"):
            return Response({"work": "Upload a PDF file."}, status=status.HTTP_400_BAD_REQUEST)
        if uploaded.read(5) != b"%PDF-":
            return Response(
                {"work": "This file does not appear to be a valid PDF."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        uploaded.seek(0)

        try:
            result = check_written_work(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
                prompt=attempt.question.prompt,
                expected_answer=attempt.question.expected_answer,
                rubric=attempt.question.rubric,
                pdf_bytes=uploaded.read(),
            )
        except GeminiWorkCheckError as error:
            return Response({"detail": str(error)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(result)


class StudentProgressView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsStudent]

    def get(self, request):
        attempts = Attempt.objects.filter(student=request.user, school=request.user.school)
        summary = attempts.aggregate(
            total=Count("id"),
            correct=Count("id", filter=Q(is_correct=True)),
            scored=Count("id", filter=Q(score__isnull=False)),
            average_score=Avg("score"),
        )
        recent = attempts.select_related("question__topic__subject")[:30]
        return Response(
            {
                "summary": {
                    "total_attempts": summary["total"] or 0,
                    "correct_attempts": summary["correct"] or 0,
                    "scored_attempts": summary["scored"] or 0,
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
        return self.create_students(request, serializer.validated_data["students"])

    @staticmethod
    def create_students(request, students):
        school = request.user.school
        usernames = [student["username"] for student in students]
        if User.objects.filter(school=school).annotate(
            normalized_username=Lower("username")
        ).filter(normalized_username__in=[username.lower() for username in usernames]).exists():
            return Response(
                {"detail": "One or more usernames are already in use at your school."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        class_ids = {
            student["class_id"]
            for student in students
            if student.get("class_id") is not None
        }
        classes = SchoolClass.objects.filter(school=school, id__in=class_ids).in_bulk()
        if class_ids != set(classes):
            return Response(
                {"detail": "Choose a class that belongs to your school."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                active_subscription = (
                    school.subscriptions.select_for_update()
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
                current_student_count = school.users.filter(
                    role=User.Role.STUDENT, is_active=True
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
                        school=school,
                        school_class=classes.get(entry.get("class_id")),
                        grade=int(entry["grade"]),
                    )
                    for entry in students
                ]
                for user, entry in zip(created, students):
                    user.set_password(entry["password"])
                User.objects.bulk_create(created)
        except IntegrityError:
            return Response(
                {"detail": "One or more usernames are already in use at your school."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {"created": len(created), "usernames": usernames},
            status=status.HTTP_201_CREATED,
        )


class BulkStudentImportView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolAdmin]
    parser_classes = [MultiPartParser, FormParser]
    max_file_size = 2 * 1024 * 1024

    def post(self, request):
        uploaded = request.FILES.get("file")
        if uploaded is None:
            return Response(
                {"detail": "Upload a CSV file in the 'file' field."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if uploaded.size > self.max_file_size:
            return Response(
                {"detail": "CSV file must be 2 MB or smaller."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            text = uploaded.read().decode("utf-8-sig")
        except UnicodeDecodeError:
            return Response(
                {"detail": "CSV file must use UTF-8 encoding."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reader = csv.DictReader(io.StringIO(text, newline=""))
            required_headers = {
                "username",
                "password",
                "first_name",
                "last_name",
                "grade",
            }
            headers = {header.strip().lower() for header in (reader.fieldnames or [])}
            if not required_headers.issubset(headers):
                return Response(
                    {"detail": "CSV must include username, password, first_name, last_name and grade columns."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            rows = []
            for row_number, raw_row in enumerate(reader, start=2):
                if len(rows) >= 200:
                    return Response(
                        {"detail": "A CSV import may contain at most 200 students."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if None in raw_row or any(
                    isinstance(value, list) for value in raw_row.values()
                ):
                    return Response(
                        {"detail": f"Row {row_number} has more columns than the header."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                row = {
                    (key or "").strip().lower(): (value or "")
                    for key, value in raw_row.items()
                }
                class_id = None
                class_name = row.get("class_name", "").strip()
                if class_name:
                    school_class = SchoolClass.objects.filter(
                        school=request.user.school, name__iexact=class_name
                    ).first()
                    if school_class is None:
                        return Response(
                            {"detail": f"Class '{class_name}' on row {row_number} does not exist at your school."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    class_id = school_class.id
                rows.append(
                    {
                        "username": row.get("username", ""),
                        "password": row.get("password", ""),
                        "first_name": row.get("first_name", ""),
                        "last_name": row.get("last_name", ""),
                        "grade": row.get("grade", "").strip(),
                        "class_id": class_id,
                    }
                )
        except (csv.Error, AttributeError):
            return Response(
                {"detail": "Could not parse the CSV file."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = BulkStudentCreateSerializer(data={"students": rows})
        serializer.is_valid(raise_exception=True)
        return BulkStudentCreateView.create_students(
            request, serializer.validated_data["students"]
        )


class SchoolStudentListView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolStaff]

    def get(self, request):
        students = User.objects.filter(
            school=request.user.school, role=User.Role.STUDENT
        ).select_related("school_class").annotate(
            total_attempts=Count("attempts", filter=Q(attempts__school=request.user.school)),
            average_score=Avg("attempts__score", filter=Q(attempts__school=request.user.school)),
        ).order_by("username")
        return Response(StudentAdminSerializer(students, many=True).data)


class SchoolStudentPerformanceView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolStaff]

    def get(self, request, student_id):
        student = User.objects.filter(
            id=student_id,
            school=request.user.school,
            role=User.Role.STUDENT,
        ).select_related("school_class").first()
        if student is None:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        attempts = Attempt.objects.filter(
            school=request.user.school,
            student=student,
        )
        summary = attempts.aggregate(
            total_attempts=Count("id"),
            correct_attempts=Count("id", filter=Q(is_correct=True)),
            scored_attempts=Count("score"),
            average_score=Avg("score"),
        )
        subject_performance = {}
        topic_rows = (
            attempts.values(
                "question__topic__subject_id",
                "question__topic__subject__name",
                "question__topic_id",
                "question__topic__title",
            )
            .annotate(
                attempts=Count("id"),
                correct_attempts=Count("id", filter=Q(is_correct=True)),
                scored_attempts=Count("score"),
                average_score=Avg("score"),
            )
            .order_by(
                "question__topic__subject__position",
                "question__topic__subject__name",
                "question__topic__position",
                "question__topic__title",
            )
        )
        for row in topic_rows:
            subject_id = row["question__topic__subject_id"]
            subject = subject_performance.setdefault(
                subject_id,
                {
                    "subject_id": subject_id,
                    "subject": row["question__topic__subject__name"],
                    "attempts": 0,
                    "correct_attempts": 0,
                    "scored_attempts": 0,
                    "average_score": None,
                    "topics": [],
                },
            )
            topic = {
                "topic_id": row["question__topic_id"],
                "topic": row["question__topic__title"],
                "attempts": row["attempts"],
                "correct_attempts": row["correct_attempts"],
                "scored_attempts": row["scored_attempts"],
                "average_score": (
                    round(row["average_score"], 1)
                    if row["average_score"] is not None
                    else None
                ),
            }
            subject["topics"].append(topic)
            subject["attempts"] += row["attempts"]
            subject["correct_attempts"] += row["correct_attempts"]
            subject["scored_attempts"] += row["scored_attempts"]

        subject_rows = (
            attempts.values(
                "question__topic__subject_id",
                "question__topic__subject__name",
            )
            .annotate(average_score=Avg("score"))
        )
        subject_averages = {
            row["question__topic__subject_id"]: row["average_score"]
            for row in subject_rows
        }
        for subject_id, subject in subject_performance.items():
            average_score = subject_averages[subject_id]
            subject["average_score"] = (
                round(average_score, 1) if average_score is not None else None
            )

        return Response(
            {
                "student": {
                    "id": student.id,
                    "username": student.username,
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "grade": student.grade,
                    "grade_label": student.get_grade_display(),
                    "class_name": (
                        student.school_class.name if student.school_class else None
                    ),
                    "is_active": student.is_active,
                },
                "summary": {
                    "total_attempts": summary["total_attempts"] or 0,
                    "correct_attempts": summary["correct_attempts"] or 0,
                    "scored_attempts": summary["scored_attempts"] or 0,
                    "average_score": (
                        round(summary["average_score"], 1)
                        if summary["average_score"] is not None
                        else None
                    ),
                },
                "subjects": list(subject_performance.values()),
            }
        )


class SchoolStudentDetailView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolAdmin]

    def get_student(self, request, student_id):
        return User.objects.filter(
            id=student_id,
            school=request.user.school,
            role=User.Role.STUDENT,
        ).first()

    def patch(self, request, student_id):
        student = self.get_student(request, student_id)
        if student is None:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_active = serializer.validated_data["is_active"]
        if is_active and not student.is_active:
            with transaction.atomic():
                subscription = (
                    request.user.school.subscriptions.select_for_update()
                    .filter(
                        status=TermSubscription.Status.ACTIVE,
                        starts_at__lte=timezone.now().date(),
                        ends_at__gte=timezone.now().date(),
                    )
                    .order_by("-seat_limit")
                    .first()
                )
                if subscription is None:
                    return Response(
                        {"detail": "No current school subscription is available."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                active_count = request.user.school.users.filter(
                    role=User.Role.STUDENT,
                    is_active=True,
                ).count()
                if active_count >= subscription.seat_limit:
                    return Response(
                        {"detail": f"This term has {subscription.seat_limit} student seats."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                student.is_active = True
                student.save(update_fields=["is_active"])
        else:
            student.is_active = is_active
            student.save(update_fields=["is_active"])
        return Response(StudentAdminSerializer(student).data)

    def post(self, request, student_id):
        if request.resolver_match.url_name != "school-student-reset-password":
            return Response(
                {"detail": "Method not allowed."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        student = self.get_student(request, student_id)
        if student is None:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentPasswordResetSerializer(
            data=request.data, context={"user": student}
        )
        serializer.is_valid(raise_exception=True)
        student.set_password(serializer.validated_data["password"])
        student.save(update_fields=["password"])
        return Response({"detail": "Student password has been reset."})


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


class SchoolTeacherCreateView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolAdmin]

    def post(self, request):
        serializer = TeacherAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        school = request.user.school
        if User.objects.filter(school=school).annotate(
            normalized_username=Lower("username")
        ).filter(normalized_username=data["username"].lower()).exists():
            return Response(
                {"username": "That username is already used at this school."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            teacher = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=User.Role.TEACHER,
                school=school,
            )
        except IntegrityError:
            return Response(
                {"username": "That username is already used at this school."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "id": teacher.id,
                "username": teacher.username,
                "first_name": teacher.first_name,
                "last_name": teacher.last_name,
                "school_name": school.name,
                "school_code": school.slug,
                "role": teacher.role,
            },
            status=status.HTTP_201_CREATED,
        )


class SchoolReportsView(APIView):
    permission_classes = [HasActiveSchoolAccess, IsSchoolStaff]

    def get(self, request):
        filters = ReportFilterSerializer(data=request.query_params)
        filters.is_valid(raise_exception=True)
        class_id = filters.validated_data.get("class_id")
        subject_id = filters.validated_data.get("subject_id")
        grade = filters.validated_data.get("grade")
        school_classes = SchoolClass.objects.filter(school=request.user.school)
        if class_id and not school_classes.filter(id=class_id).exists():
            return Response({"detail": "Class not found."}, status=status.HTTP_404_NOT_FOUND)
        if subject_id and not Subject.objects.filter(id=subject_id, is_published=True).exists():
            return Response({"detail": "Subject not found."}, status=status.HTTP_404_NOT_FOUND)

        attempts = Attempt.objects.filter(school=request.user.school)
        if class_id:
            attempts = attempts.filter(student__school_class_id=class_id)
        if grade:
            attempts = attempts.filter(student__grade=grade)
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
        if grade:
            student_query = student_query.filter(grade=grade)
        if subject_id:
            student_attempt_filter &= Q(attempts__question__topic__subject_id=subject_id)
        students = (
            student_query
            .annotate(
                total_attempts=Count("attempts", filter=student_attempt_filter),
                average_score=Avg("attempts__score", filter=student_attempt_filter),
                class_name=F("school_class__name"),
            )
            .values(
                "id",
                "username",
                "first_name",
                "last_name",
                "is_active",
                "class_name",
                "grade",
                "total_attempts",
                "average_score",
            )
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
                    role=User.Role.STUDENT, is_active=True
                ).count(),
                "inactive_student_count": request.user.school.users.filter(
                    role=User.Role.STUDENT, is_active=False
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
