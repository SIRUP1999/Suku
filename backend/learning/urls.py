from django.urls import path

from .views import (
    AttemptView,
    BulkStudentCreateView,
    SchoolReportsView,
    SchoolClassesView,
    StudentProgressView,
    SubjectListView,
    SubjectTopicsView,
    TopicQuestionsView,
)

urlpatterns = [
    path("subjects/", SubjectListView.as_view(), name="subject-list"),
    path("subjects/<int:subject_id>/topics/", SubjectTopicsView.as_view(), name="subject-topics"),
    path("topics/<int:topic_id>/questions/", TopicQuestionsView.as_view(), name="topic-questions"),
    path("attempts/", AttemptView.as_view(), name="attempt-submit"),
    path("progress/", StudentProgressView.as_view(), name="student-progress"),
    path("admin/students/bulk-create/", BulkStudentCreateView.as_view(), name="bulk-students"),
    path("admin/classes/", SchoolClassesView.as_view(), name="school-classes"),
    path("admin/reports/", SchoolReportsView.as_view(), name="school-reports"),
]
