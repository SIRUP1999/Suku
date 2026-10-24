import base64
import json
from datetime import timedelta
from unittest.mock import MagicMock, patch
from urllib.request import Request

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from learning.models import Attempt, Question, Subject, Topic
from learning.ai import check_written_work
from schools.models import School, SchoolClass, TermSubscription, User


class GeminiWorkCheckTests(SimpleTestCase):
    @patch("learning.ai.urlopen")
    def test_pdf_is_sent_as_inline_data_and_structured_result_is_returned(self, urlopen):
        assessment = {
            "status": "partly_correct",
            "feedback": "Your first step is right; check the sign in the second step.",
            "worked_solution": "Correct working goes here.",
        }
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"candidates": [{"content": {"parts": [{"text": json.dumps(assessment)}]}}]}
        ).encode("utf-8")
        urlopen.return_value = response

        result = check_written_work(
            api_key="server-secret",
            model="gemini-test",
            prompt="Solve 2 + 2.",
            expected_answer="4",
            rubric="Show addition.",
            pdf_bytes=b"%PDF-test",
        )

        self.assertEqual(result, assessment)
        request = urlopen.call_args.args[0]
        self.assertIsInstance(request, Request)
        self.assertEqual(request.get_header("X-goog-api-key"), "server-secret")
        payload = json.loads(request.data)
        pdf_part = payload["contents"][0]["parts"][1]["inlineData"]
        self.assertEqual(pdf_part["mimeType"], "application/pdf")
        self.assertEqual(pdf_part["data"], base64.b64encode(b"%PDF-test").decode("ascii"))


class LearningFlowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.school = School.objects.create(name="Akan School", slug="akan-school")
        self.student = User.objects.create_user(
            username="ama",
            password="a-safe-password",
            role=User.Role.STUDENT,
            school=self.school,
        )
        self.subject = Subject.objects.get(slug="mathematics")
        self.topic = Topic.objects.create(
            subject=self.subject,
            title="Fractions",
            slug="fractions",
            grade=7,
            term=1,
            is_published=True,
        )
        self.question = Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.MCQ,
            prompt="What is one half of 8?",
            options=["2", "4", "6"],
            correct_answer="4",
            explanation="Divide 8 into two equal groups.",
            is_published=True,
        )

    def activate_school(self, seat_limit=20):
        self.school.status = School.Status.ACTIVE
        self.school.save(update_fields=["status"])
        today = timezone.now().date()
        return TermSubscription.objects.create(
            school=self.school,
            term_name="Term 1",
            starts_at=today - timedelta(days=1),
            ends_at=today + timedelta(days=90),
            seat_limit=seat_limit,
            status=TermSubscription.Status.ACTIVE,
        )

    def test_school_must_have_current_subscription_to_login(self):
        response = self.client.post(
            reverse("login"),
            {"school_code": "akan-school", "username": "ama", "password": "a-safe-password"},
        )
        self.assertEqual(response.status_code, 403)

        self.activate_school()
        response = self.client.post(
            reverse("login"),
            {"school_code": "akan-school", "username": "ama", "password": "a-safe-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_school_admin_can_register_school_pending_approval(self):
        response = self.client.post(
            reverse("register-school"),
            {
                "school_name": "New Learning Academy",
                "first_name": "Abena",
                "last_name": "Mensah",
                "username": "headteacher",
                "password": "Long-Secure-Pass-954!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        school = School.objects.get(slug=response.data["school_code"])
        admin = User.objects.get(school=school)
        self.assertEqual(school.status, School.Status.PENDING)
        self.assertEqual(admin.role, User.Role.SCHOOL_ADMIN)
        self.assertEqual((admin.first_name, admin.last_name), ("Abena", "Mensah"))
        self.assertEqual(response.data["school_name"], school.name)
        self.assertNotIn("access", response.data)
        pending_login = self.client.post(
            reverse("login"),
            {
                "school_code": school.slug,
                "username": admin.username,
                "password": "Long-Secure-Pass-954!",
            },
            format="json",
        )
        self.assertEqual(pending_login.status_code, 403)

    def test_student_signup_uses_school_code_and_saves_grade(self):
        self.activate_school(seat_limit=2)
        response = self.client.post(
            reverse("register-student"),
            {
                "school_code": self.school.slug,
                "first_name": "Ama",
                "last_name": "Owusu",
                "username": "ama-new",
                "password": "Long-Student-Pass-846!",
                "grade": 8,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        student = User.objects.get(school=self.school, username="ama-new")
        self.assertEqual(student.grade, 8)
        self.assertEqual(student.school, self.school)
        self.assertEqual(response.data["user"]["school_name"], self.school.name)
        self.assertEqual(response.data["user"]["grade"], 8)
        self.assertTrue(response.data["access"])

    def test_student_signup_rejects_another_schools_code_and_full_seats(self):
        self.activate_school(seat_limit=1)
        self.school.status = School.Status.ACTIVE
        self.school.save(update_fields=["status"])
        response = self.client.post(
            reverse("register-student"),
            {
                "school_code": "not-a-school",
                "first_name": "Kojo",
                "last_name": "Asare",
                "username": "kojo-new",
                "password": "Long-Student-Pass-846!",
                "grade": 7,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="kojo-new").exists())

        response = self.client.post(
            reverse("register-student"),
            {
                "school_code": self.school.slug,
                "first_name": "Kojo",
                "last_name": "Asare",
                "username": "kojo-new",
                "password": "Long-Student-Pass-846!",
                "grade": 7,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="kojo-new").exists())

    def test_reports_can_be_filtered_by_grade(self):
        self.activate_school()
        self.student.grade = 8
        self.student.save(update_fields=["grade"])
        admin = User.objects.create_user(
            username="report-admin",
            password="a-safe-admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)

        grade_eight = self.client.get(reverse("school-reports") + "?grade=8")
        self.assertEqual(grade_eight.status_code, 200)
        self.assertEqual([row["id"] for row in grade_eight.data["students"]], [self.student.id])
        grade_nine = self.client.get(reverse("school-reports") + "?grade=9")
        self.assertEqual(grade_nine.status_code, 200)
        self.assertEqual(grade_nine.data["students"], [])
        invalid_grade = self.client.get(reverse("school-reports") + "?grade=10")
        self.assertEqual(invalid_grade.status_code, 400)

    def test_teacher_can_login_and_view_only_their_school_performance(self):
        self.activate_school()
        self.student.grade = 9
        self.student.save(update_fields=["grade"])
        teacher = User.objects.create_user(
            username="teacher",
            password="Long-Teacher-Pass-846!",
            first_name="Esi",
            last_name="Teacher",
            role=User.Role.TEACHER,
            school=self.school,
        )
        login = self.client.post(
            reverse("login"),
            {
                "school_code": self.school.slug,
                "username": teacher.username,
                "password": "Long-Teacher-Pass-846!",
            },
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.data["user"]["school_name"], self.school.name)

        other_school = School.objects.create(
            name="Other School", slug="other-school", status=School.Status.ACTIVE
        )
        other_student = User.objects.create_user(
            username="other-student",
            password="a-safe-other-password",
            first_name="Other",
            last_name="Learner",
            role=User.Role.STUDENT,
            school=other_school,
            grade=7,
        )
        Attempt.objects.create(
            school=other_school,
            student=other_student,
            question=self.question,
            submitted_answer="4",
            is_correct=True,
            score=100,
        )
        self.client.force_authenticate(teacher)
        report = self.client.get(reverse("school-reports"))
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.data["school"], self.school.name)
        self.assertEqual(
            [row["id"] for row in report.data["students"]],
            [self.student.id],
        )
        self.assertEqual(report.data["summary"]["total_attempts"], 0)

        student_list = self.client.get(reverse("school-students"))
        self.assertEqual(student_list.status_code, 200)
        self.assertEqual([row["id"] for row in student_list.data], [self.student.id])
        self.assertEqual(student_list.data[0]["grade"], 9)
        own_performance = self.client.get(
            reverse("school-student-performance", kwargs={"student_id": self.student.id})
        )
        self.assertEqual(own_performance.status_code, 200)
        self.assertEqual(own_performance.data["student"]["grade"], 9)
        self.assertEqual(
            self.client.get(
                reverse("school-student-performance", kwargs={"student_id": other_student.id})
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.patch(
                reverse("school-student-detail", kwargs={"student_id": self.student.id}),
                {"is_active": False},
                format="json",
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                reverse("school-teachers"),
                {
                    "username": "unauthorized-teacher",
                    "password": "Long-Teacher-Pass-846!",
                    "first_name": "Ama",
                    "last_name": "Teacher",
                },
                format="json",
            ).status_code,
            403,
        )
        school_admin = User.objects.create_user(
            username="school-admin",
            password="a-safe-admin-password",
            first_name="School",
            last_name="Admin",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(school_admin)
        create_teacher = self.client.post(
            reverse("school-teachers"),
            {
                "username": "created-teacher",
                "password": "Long-Teacher-Pass-846!",
                "first_name": "Ama",
                "last_name": "Teacher",
            },
            format="json",
        )
        self.assertEqual(create_teacher.status_code, 201)
        self.assertEqual(create_teacher.data["role"], User.Role.TEACHER)
        self.assertEqual(User.objects.get(username="created-teacher").school, self.school)


    def test_same_username_can_exist_in_separate_schools_and_login_is_school_scoped(self):
        self.activate_school()
        other_school = School.objects.create(
            name="Coastal School", slug="coastal-school", status=School.Status.ACTIVE
        )
        today = timezone.now().date()
        TermSubscription.objects.create(
            school=other_school,
            term_name="Term 1",
            starts_at=today - timedelta(days=1),
            ends_at=today + timedelta(days=90),
            seat_limit=10,
            status=TermSubscription.Status.ACTIVE,
        )
        another_ama = User.objects.create_user(
            username="ama",
            password="another-safe-password",
            role=User.Role.STUDENT,
            school=other_school,
        )
        response = self.client.post(
            reverse("login"),
            {"school_code": "coastal-school", "username": "ama", "password": "another-safe-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["id"], another_ama.id)
        response = self.client.post(
            reverse("login"),
            {"school_code": "akan-school", "username": "ama", "password": "another-safe-password"},
        )
        self.assertEqual(response.status_code, 401)

    def test_login_rate_limits_by_username_without_blocking_a_class_ip(self):
        self.activate_school()
        response_codes = []
        for index in range(35):
            response = self.client.post(
                reverse("login"),
                {
                    "school_code": "akan-school",
                    "username": f"student-{index}",
                    "password": "incorrect-password",
                },
            )
            response_codes.append(response.status_code)
        self.assertNotIn(429, response_codes)

        statuses = []
        for _ in range(11):
            response = self.client.post(
                reverse("login"),
                {
                    "school_code": "akan-school",
                    "username": "same-user",
                    "password": "incorrect-password",
                },
            )
            statuses.append(response.status_code)
        self.assertEqual(statuses[-1], 429)

    def test_mcq_attempt_returns_feedback_and_is_scoped_to_student_school(self):
        self.activate_school()
        self.client.force_authenticate(self.student)
        question_response = self.client.get(
            reverse("topic-questions", kwargs={"topic_id": self.topic.id})
        )
        self.assertEqual(question_response.status_code, 200)
        self.assertNotIn("correct_answer", question_response.data[0])

        response = self.client.post(
            reverse("attempt-submit"),
            {"question_id": self.question.id, "answer": "2"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data["is_correct"])
        self.assertEqual(response.data["correct_answer"], "4")
        self.assertEqual(Attempt.objects.get().school, self.school)

    def test_grade_filter_and_mixed_question_kinds_are_available(self):
        self.activate_school()
        grade_eight_topic = Topic.objects.create(
            subject=self.subject,
            title="Algebra",
            slug="grade-eight-algebra",
            grade=8,
            term=1,
            is_published=True,
        )
        Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.THEORY,
            prompt="Work out half of 8 on paper.",
            options=["2", "4", "6"],
            correct_answer="4",
            expected_answer="8 ÷ 2 = 4",
            explanation="Divide 8 into two equal groups: 8 ÷ 2 = 4.",
            is_published=True,
        )
        Question.objects.create(
            topic=grade_eight_topic,
            kind=Question.Kind.MCQ,
            prompt="A Grade 8 question",
            options=["1", "2"],
            correct_answer="2",
            is_published=True,
        )
        self.client.force_authenticate(self.student)

        response = self.client.get(
            reverse("subject-topics", kwargs={"subject_id": self.subject.id}) + "?grade=7"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)
        self.assertTrue(all(row["grade"] == 7 for row in response.data))
        self.assertIn(self.topic.id, {row["id"] for row in response.data})

        questions = self.client.get(
            reverse("topic-questions", kwargs={"topic_id": self.topic.id})
        )
        self.assertEqual(
            {row["kind"] for row in questions.data},
            {Question.Kind.MCQ, Question.Kind.THEORY},
        )
        self.assertNotIn("correct_answer", questions.data[0])
        self.assertFalse(questions.data[0]["work_check_available"])

    def test_theory_answer_shows_correct_working_for_wrong_answer(self):
        self.activate_school()
        theory = Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.THEORY,
            prompt="Work out half of 8 on paper.",
            options=["2", "4", "6"],
            correct_answer="4",
            expected_answer="8 ÷ 2 = 4",
            explanation="Divide 8 into two equal groups: 8 ÷ 2 = 4.",
            is_published=True,
        )
        self.client.force_authenticate(self.student)

        response = self.client.post(
            reverse("attempt-submit"),
            {"question_id": theory.id, "answer": "2"},
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data["is_correct"])
        self.assertEqual(response.data["correct_answer"], "4")
        self.assertEqual(
            response.data["worked_solution"],
            "Divide 8 into two equal groups: 8 ÷ 2 = 4.",
        )
        self.assertEqual(response.data["question_kind"], Question.Kind.THEORY)

        correct_response = self.client.post(
            reverse("attempt-submit"),
            {"question_id": theory.id, "answer": "4"},
        )
        self.assertTrue(correct_response.data["is_correct"])
        self.assertEqual(
            correct_response.data["worked_solution"],
            "Divide 8 into two equal groups: 8 ÷ 2 = 4.",
        )

    def test_structured_written_answer_is_saved_without_automatic_marking(self):
        self.activate_school()
        theory = Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.THEORY,
            prompt="(a) Find the perimeter of a rectangle. [2 marks]",
            options=[],
            expected_answer="Perimeter = 2(length + width).",
            rubric="Award marks for the formula and correct substitution.",
            explanation="Step 1: Add the length and width.\nStep 2: Double the total.",
            is_published=True,
        )
        theory.full_clean()
        self.client.force_authenticate(self.student)

        response = self.client.post(
            reverse("attempt-submit"),
            {"question_id": theory.id, "answer": "My formula is 2 × (length + width)."},
        )

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["is_correct"])
        self.assertIsNone(response.data["score"])
        self.assertIn("not marked automatically", response.data["feedback"])
        self.assertEqual(
            response.data["mark_guide"],
            "Award marks for the formula and correct substitution.",
        )
        self.assertEqual(
            Attempt.objects.get(question=theory).submitted_answer,
            "My formula is 2 × (length + width).",
        )
        progress = self.client.get(reverse("student-progress"))
        self.assertEqual(progress.data["summary"]["scored_attempts"], 0)

    def test_structured_written_answer_cannot_be_empty(self):
        self.activate_school()
        theory = Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.THEORY,
            prompt="Show your working.",
            options=[],
            expected_answer="A worked solution.",
            explanation="Step 1: Work carefully.",
            is_published=True,
        )
        self.client.force_authenticate(self.student)

        response = self.client.post(
            reverse("attempt-submit"), {"question_id": theory.id, "answer": "  "}
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Attempt.objects.filter(question=theory).exists())

    @override_settings(GEMINI_API_KEY="")
    def test_pdf_work_check_reports_when_gemini_is_not_configured(self):
        self.activate_school()
        theory = Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.THEORY,
            prompt="Work out half of 8 on paper.",
            options=["2", "4", "6"],
            correct_answer="4",
            expected_answer="8 ÷ 2 = 4",
            is_published=True,
        )
        self.client.force_authenticate(self.student)
        attempt = self.client.post(
            reverse("attempt-submit"),
            {"question_id": theory.id, "answer": "4"},
        )
        pdf = SimpleUploadedFile("work.pdf", b"%PDF-1.4 sample", content_type="application/pdf")

        response = self.client.post(
            reverse("attempt-work-check", kwargs={"attempt_id": attempt.data["id"]}),
            {"work": pdf},
            format="multipart",
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn("not configured", response.data["detail"])

    @override_settings(GEMINI_API_KEY="test-api-key")
    @patch("learning.views.check_written_work")
    def test_theory_work_pdf_is_sent_for_check_without_persisting_file(self, check_work):
        self.activate_school()
        theory = Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.THEORY,
            prompt="Work out half of 8 on paper.",
            options=["2", "4", "6"],
            correct_answer="4",
            expected_answer="8 ÷ 2 = 4",
            explanation="Divide 8 into two equal groups: 8 ÷ 2 = 4.",
            is_published=True,
        )
        self.client.force_authenticate(self.student)
        attempt_response = self.client.post(
            reverse("attempt-submit"),
            {"question_id": theory.id, "answer": "4"},
        )
        self.assertEqual(attempt_response.status_code, 201)
        pdf = SimpleUploadedFile("work.pdf", b"%PDF-1.4 sample", content_type="application/pdf")
        check_work.return_value = {
            "status": "correct",
            "feedback": "Your steps are correct.",
            "worked_solution": "8 ÷ 2 = 4.",
        }

        response = self.client.post(
            reverse("attempt-work-check", kwargs={"attempt_id": attempt_response.data["id"]}),
            {"work": pdf},
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "correct")
        check_work.assert_called_once_with(
            api_key="test-api-key",
            model="gemini-2.5-flash",
            prompt="Work out half of 8 on paper.",
            expected_answer="8 ÷ 2 = 4",
            rubric="",
            pdf_bytes=b"%PDF-1.4 sample",
        )

    def test_seeded_math_topics_have_published_mcq_and_theory_items_for_each_grade(self):
        topics = Topic.objects.filter(
            subject=self.subject,
            grade__in=(7, 8, 9),
            slug__startswith="g",
            is_published=True,
        ).exclude(slug="g9-paper-2-written-practice").prefetch_related("questions")
        self.assertTrue(topics.exists())
        grades = set()
        for topic in topics:
            grades.add(topic.grade)
            self.assertEqual(
                topic.questions.filter(is_published=True, kind=Question.Kind.MCQ).count(),
                40,
                topic.title,
            )
            self.assertEqual(
                topic.questions.filter(
                    is_published=True,
                    kind=Question.Kind.MCQ,
                ).values_list("prompt", flat=True).distinct().count(),
                40,
                topic.title,
            )
            self.assertEqual(
                topic.questions.filter(is_published=True, kind=Question.Kind.THEORY).count(),
                10,
                topic.title,
            )
            objective_difficulties = {
                difficulty: topic.questions.filter(
                    is_published=True,
                    kind=Question.Kind.MCQ,
                    difficulty=difficulty,
                ).count()
                for difficulty in (
                    Question.Difficulty.EASY,
                    Question.Difficulty.MEDIUM,
                    Question.Difficulty.HARD,
                )
            }
            self.assertEqual(objective_difficulties, {"easy": 10, "medium": 20, "hard": 10})
            for question in topic.questions.filter(is_published=True):
                self.assertEqual(len(question.options), 4, question.prompt)
                self.assertEqual(len(question.options), len(set(question.options)), question.prompt)
                self.assertIn(question.correct_answer, question.options, question.prompt)
                self.assertIn("Step 1:", question.explanation, question.prompt)
                if question.kind == Question.Kind.THEORY:
                    self.assertNotIn("BECE-style structured practice", question.prompt, topic.title)
                    self.assertNotIn("(a) State the rule", question.prompt, topic.title)
                    self.assertNotIn("(c) Choose the option", question.prompt, topic.title)
                    self.assertIn("Total: 4 marks.", question.rubric, topic.title)
                self.assertFalse(
                    question.prompt.startswith(
                        "Show your working step by step on paper before choosing an answer."
                    ),
                    question.prompt,
                )
        self.assertEqual(grades, {7, 8, 9})

        paper_topic = Topic.objects.get(
            subject=self.subject,
            slug="g9-paper-2-written-practice",
            is_published=True,
        )
        paper_questions = list(paper_topic.questions.filter(is_published=True))
        self.assertEqual(len(paper_questions), 6)
        self.assertEqual(
            {question.difficulty for question in paper_questions},
            {Question.Difficulty.MEDIUM, Question.Difficulty.HARD},
        )
        self.assertTrue(all(question.kind == Question.Kind.THEORY for question in paper_questions))
        self.assertTrue(all(len(question.options) == 4 for question in paper_questions))
        self.assertTrue(
            all(question.correct_answer in question.options for question in paper_questions)
        )
        self.assertTrue(
            all("Step 1:" in question.explanation for question in paper_questions)
        )

    def test_expired_subscription_blocks_student_endpoints(self):
        self.school.status = School.Status.ACTIVE
        self.school.save(update_fields=["status"])
        yesterday = timezone.now().date() - timedelta(days=1)
        TermSubscription.objects.create(
            school=self.school,
            term_name="Expired term",
            starts_at=yesterday - timedelta(days=90),
            ends_at=yesterday,
            seat_limit=20,
            status=TermSubscription.Status.ACTIVE,
        )
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("subject-list"))
        self.assertEqual(response.status_code, 403)

    def test_unpublished_questions_are_not_returned(self):
        self.activate_school()
        Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.MCQ,
            prompt="Draft question",
            options=["A", "B"],
            correct_answer="A",
            is_published=False,
        )
        self.client.force_authenticate(self.student)
        response = self.client.get(reverse("topic-questions", kwargs={"topic_id": self.topic.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([question["id"] for question in response.data], [self.question.id])

    def test_student_cannot_access_admin_endpoints_and_admin_cannot_fetch_practice(self):
        self.activate_school()
        self.client.force_authenticate(self.student)
        self.assertEqual(self.client.get(reverse("school-reports")).status_code, 403)
        self.assertEqual(self.client.get(reverse("school-classes")).status_code, 403)
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        self.assertEqual(
            self.client.get(
                reverse("topic-questions", kwargs={"topic_id": self.topic.id})
            ).status_code,
            403,
        )

    def test_school_admin_cannot_exceed_paid_student_seats(self):
        subscription = self.activate_school(seat_limit=1)
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        response = self.client.post(
            reverse("bulk-students"),
            {
                "students": [
                    {
                        "username": "kojo",
                        "password": "Long-Student-Pass-846!",
                        "first_name": "Kojo",
                        "last_name": "Asare",
                        "grade": 7,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(str(subscription.seat_limit), response.data["detail"])
        self.assertFalse(User.objects.filter(username="kojo").exists())

    def test_school_admin_can_create_students_and_assign_school_classes(self):
        self.activate_school(seat_limit=10)
        classroom = SchoolClass.objects.create(school=self.school, name="JHS 2B")
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        response = self.client.post(
            reverse("bulk-students"),
            {
                "students": [
                    {
                        "username": "newstudent",
                        "password": "Long-Temp-Pass-492!",
                        "first_name": "Kojo",
                        "last_name": "Mensah",
                        "grade": 8,
                        "class_id": classroom.id,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["created"], 1)
        student = User.objects.get(username="newstudent")
        self.assertEqual(student.school, self.school)
        self.assertEqual(student.school_class, classroom)
        self.assertEqual(student.grade, 8)
        self.assertTrue(student.check_password("Long-Temp-Pass-492!"))

    def test_admin_cannot_assign_another_schools_class(self):
        self.activate_school()
        other_school = School.objects.create(name="Other School", slug="other-school")
        foreign_class = SchoolClass.objects.create(school=other_school, name="JHS 1")
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        response = self.client.post(
            reverse("bulk-students"),
            {
                "students": [
                    {
                        "username": "kojo",
                        "password": "Long-Temp-Pass-492!",
                        "first_name": "Kojo",
                        "last_name": "Asare",
                        "grade": 7,
                        "class_id": foreign_class.id,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(school=self.school, username="kojo").exists())

    def test_admin_cannot_manage_another_schools_student(self):
        self.activate_school()
        other_school = School.objects.create(name="Other School", slug="other-school")
        foreign_student = User.objects.create_user(
            username="foreign",
            password="another-password",
            role=User.Role.STUDENT,
            school=other_school,
        )
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        response = self.client.patch(
            reverse("school-student-detail", kwargs={"student_id": foreign_student.id}),
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.post(
            reverse("school-student-reset-password", kwargs={"student_id": foreign_student.id}),
            {"password": "New-Safe-Password-492!"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        foreign_student.refresh_from_db()
        self.assertTrue(foreign_student.is_active)
        self.assertTrue(foreign_student.check_password("another-password"))

    def test_admin_can_deactivate_reset_and_reactivate_a_student(self):
        self.activate_school(seat_limit=2)
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        status_url = reverse("school-student-detail", kwargs={"student_id": self.student.id})
        response = self.client.patch(status_url, {"is_active": False}, format="json")
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)

        response = self.client.post(
            reverse("school-student-reset-password", kwargs={"student_id": self.student.id}),
            {"password": "New-Safe-Password-492!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertTrue(self.student.check_password("New-Safe-Password-492!"))

        response = self.client.patch(status_url, {"is_active": True}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_deactivated_student_frees_seat_and_reactivation_respects_limit(self):
        self.activate_school(seat_limit=1)
        second_student = User.objects.create_user(
            username="kojo",
            password="another-password",
            role=User.Role.STUDENT,
            school=self.school,
            is_active=False,
        )
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        response = self.client.patch(
            reverse("school-student-detail", kwargs={"student_id": self.student.id}),
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(
            reverse("school-student-detail", kwargs={"student_id": second_student.id}),
            {"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.school.users.filter(role=User.Role.STUDENT, is_active=True).count(),
            1,
        )

        response = self.client.patch(
            reverse("school-student-detail", kwargs={"student_id": self.student.id}),
            {"is_active": True},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_csv_import_creates_school_scoped_students(self):
        self.activate_school()
        classroom = SchoolClass.objects.create(school=self.school, name="JHS 1")
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        content = (
            "username,password,first_name,last_name,grade,class_name\n"
            "csv-ama,Long-Temp-Pass-492!,Ama,Mensah,7,JHS 1\n"
        )
        upload = SimpleUploadedFile("students.csv", content.encode(), content_type="text/csv")
        response = self.client.post(reverse("bulk-student-import"), {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, 201)
        student = User.objects.get(school=self.school, username="csv-ama")
        self.assertEqual(student.school_class, classroom)
        self.assertEqual(student.grade, 7)
        self.assertTrue(student.check_password("Long-Temp-Pass-492!"))

    def test_school_reports_can_filter_by_class_and_subject_without_cross_tenant_data(self):
        self.activate_school()
        classroom = SchoolClass.objects.create(school=self.school, name="JHS 1A")
        self.student.school_class = classroom
        self.student.save(update_fields=["school_class"])
        Attempt.objects.create(
            school=self.school,
            student=self.student,
            question=self.question,
            submitted_answer="4",
            is_correct=True,
            score=100,
        )
        other_school = School.objects.create(name="Other School", slug="other-school")
        other_student = User.objects.create_user(
            username="other-student",
            password="another-password",
            role=User.Role.STUDENT,
            school=other_school,
        )
        Attempt.objects.create(
            school=other_school,
            student=other_student,
            question=self.question,
            submitted_answer="2",
            is_correct=False,
            score=0,
        )
        admin = User.objects.create_user(
            username="admin",
            password="admin-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        response = self.client.get(reverse("school-reports"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["total_attempts"], 1)
        self.assertEqual(response.data["student_count"], 1)

        response = self.client.get(
            reverse("school-reports"),
            {"class_id": classroom.id, "subject_id": self.subject.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["total_attempts"], 1)
        self.assertEqual(response.data["classes"], [{"id": classroom.id, "name": "JHS 1A"}])

        response = self.client.get(reverse("school-reports"), {"class_id": 99999})
        self.assertEqual(response.status_code, 404)

    def test_student_performance_report_shows_subject_and_topic_breakdown(self):
        self.activate_school()
        second_question = Question.objects.create(
            topic=self.topic,
            kind=Question.Kind.MCQ,
            prompt="What is one third of 9?",
            options=["2", "3", "4"],
            correct_answer="3",
            is_published=True,
        )
        Attempt.objects.create(
            school=self.school,
            student=self.student,
            question=self.question,
            submitted_answer="4",
            is_correct=True,
            score=100,
        )
        Attempt.objects.create(
            school=self.school,
            student=self.student,
            question=second_question,
            submitted_answer="2",
            is_correct=False,
            score=0,
        )
        admin = User.objects.create_user(
            username="admin",
            password="a-safe-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)

        response = self.client.get(
            reverse(
                "school-student-performance",
                kwargs={"student_id": self.student.id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["student"]["username"], "ama")
        self.assertEqual(response.data["summary"]["total_attempts"], 2)
        self.assertEqual(response.data["summary"]["correct_attempts"], 1)
        self.assertEqual(response.data["summary"]["average_score"], 50)
        self.assertEqual(len(response.data["subjects"]), 1)
        self.assertEqual(response.data["subjects"][0]["subject"], "Mathematics")
        self.assertEqual(response.data["subjects"][0]["average_score"], 50)
        self.assertEqual(response.data["subjects"][0]["topics"][0]["topic"], "Fractions")
        self.assertEqual(response.data["subjects"][0]["topics"][0]["attempts"], 2)

    def test_student_performance_report_is_school_scoped_and_admin_only(self):
        self.activate_school()
        other_school = School.objects.create(name="Other School", slug="other-school")
        other_student = User.objects.create_user(
            username="other-student",
            password="a-safe-password",
            role=User.Role.STUDENT,
            school=other_school,
        )
        admin = User.objects.create_user(
            username="admin",
            password="a-safe-password",
            role=User.Role.SCHOOL_ADMIN,
            school=self.school,
        )
        self.client.force_authenticate(admin)
        response = self.client.get(
            reverse(
                "school-student-performance",
                kwargs={"student_id": other_student.id},
            )
        )
        self.assertEqual(response.status_code, 404)

        self.client.force_authenticate(self.student)
        response = self.client.get(
            reverse(
                "school-student-performance",
                kwargs={"student_id": self.student.id},
            )
        )
        self.assertEqual(response.status_code, 403)
