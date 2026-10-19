from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from rest_framework.test import APITestCase

from learning.models import Attempt, Question, Subject, Topic
from schools.models import School, SchoolClass, TermSubscription, User


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
            subject=self.subject, title="Fractions", slug="fractions", is_published=True
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
            {"students": [{"username": "kojo", "password": "student-password"}]},
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
            "username,password,first_name,last_name,class_name\n"
            "csv-ama,Long-Temp-Pass-492!,Ama,Mensah,JHS 1\n"
        )
        upload = SimpleUploadedFile("students.csv", content.encode(), content_type="text/csv")
        response = self.client.post(reverse("bulk-student-import"), {"file": upload}, format="multipart")
        self.assertEqual(response.status_code, 201)
        student = User.objects.get(school=self.school, username="csv-ama")
        self.assertEqual(student.school_class, classroom)
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
