from django.urls import path

from .views import (
    AttemptView,
    BulkStudentCreateView,
    BulkStudentImportView,
    SchoolReportsView,
    SchoolClassesView,
    SchoolStudentDetailView,
    SchoolStudentListView,
    SchoolStudentPerformanceView,
    StudentProgressView,
    SubjectListView,
    SubjectTopicsView,
    TopicDetailView,
    TopicQuestionsView,
)

urlpatterns = [
    path("subjects/", SubjectListView.as_view(), name="subject-list"),
    path("subjects/<int:subject_id>/topics/", SubjectTopicsView.as_view(), name="subject-topics"),
    path("topics/<int:topic_id>/", TopicDetailView.as_view(), name="topic-detail"),
    path("topics/<int:topic_id>/questions/", TopicQuestionsView.as_view(), name="topic-questions"),
    path("attempts/", AttemptView.as_view(), name="attempt-submit"),
    path("progress/", StudentProgressView.as_view(), name="student-progress"),
    path("admin/students/bulk-create/", BulkStudentCreateView.as_view(), name="bulk-students"),
    path("admin/students/import/", BulkStudentImportView.as_view(), name="bulk-student-import"),
    path("admin/students/", SchoolStudentListView.as_view(), name="school-students"),
    path(
        "admin/students/<int:student_id>/performance/",
        SchoolStudentPerformanceView.as_view(),
        name="school-student-performance",
    ),
    path(
        "admin/students/<int:student_id>/",
        SchoolStudentDetailView.as_view(),
        name="school-student-detail",
    ),
    path(
        "admin/students/<int:student_id>/reset-password/",
        SchoolStudentDetailView.as_view(),
        name="school-student-reset-password",
    ),
    path("admin/classes/", SchoolClassesView.as_view(), name="school-classes"),
    path("admin/reports/", SchoolReportsView.as_view(), name="school-reports"),
]
