from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from learning.models import Attempt, Question, Subject, Topic
from schools.models import School, SchoolClass, TermSubscription, User


class LearningFlowTests(APITestCase):
    def setUp(self):
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
            reverse("login"), {"username": "ama", "password": "a-safe-password"}
        )
        self.assertEqual(response.status_code, 403)

        self.activate_school()
        response = self.client.post(
            reverse("login"), {"username": "ama", "password": "a-safe-password"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

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
