from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from schools.models import School


class Subject(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("position", "name")

    def __str__(self):
        return self.name


class Topic(models.Model):
    class Grade(models.IntegerChoices):
        GRADE_7 = 7, "Grade 7 / JHS 1"
        GRADE_8 = 8, "Grade 8 / JHS 2"
        GRADE_9 = 9, "Grade 9 / JHS 3"

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True)
    grade = models.PositiveSmallIntegerField(choices=Grade.choices, null=True, blank=True)
    term = models.PositiveSmallIntegerField(
        choices=((1, "Term 1"), (2, "Term 2"), (3, "Term 3")),
        null=True,
        blank=True,
    )
    position = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("position", "title")
        constraints = [
            models.UniqueConstraint(fields=("subject", "slug"), name="unique_topic_slug_per_subject")
        ]

    def __str__(self):
        return f"{self.subject}: {self.title}"


class Question(models.Model):
    class Kind(models.TextChoices):
        MCQ = "mcq", "Multiple choice"
        THEORY = "theory", "Theory / short answer"

    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="questions")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    prompt = models.TextField()
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField(blank=True)
    expected_answer = models.TextField(blank=True)
    rubric = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(
        max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return f"{self.topic} — {self.prompt[:70]}"

    def clean(self):
        super().clean()
        valid_options = (
            isinstance(self.options, list)
            and len(self.options) >= 2
            and all(isinstance(option, str) for option in self.options)
            and len(self.options) == len(set(self.options))
        )
        if self.kind == self.Kind.MCQ:
            if not valid_options:
                raise ValidationError({"options": "MCQs need at least two answer options."})
            if self.correct_answer not in self.options:
                raise ValidationError(
                    {"correct_answer": "Choose the correct answer from the options."}
                )
        elif self.kind == self.Kind.THEORY:
            if not (self.expected_answer or self.rubric):
                raise ValidationError(
                    {"rubric": "Theory questions need an expected answer or grading rubric."}
                )
            if not self.options:
                if self.correct_answer:
                    raise ValidationError(
                        {"correct_answer": "Free-response questions do not have a single correct answer option."}
                    )
                return
            if not valid_options:
                raise ValidationError(
                    {"options": "Written-work questions need at least two answer choices."}
                )
            if self.correct_answer not in self.options:
                raise ValidationError(
                    {"correct_answer": "Choose the correct answer from the options."}
                )


class Attempt(models.Model):
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="attempts")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts"
    )
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name="attempts")
    submitted_answer = models.TextField()
    is_correct = models.BooleanField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("school", "student", "created_at")),
            models.Index(fields=("school", "question")),
        ]

    def clean(self):
        super().clean()
        if self.student_id and self.school_id and self.student.school_id != self.school_id:
            raise ValidationError({"school": "Attempt school must match the student's school."})

    def __str__(self):
        return f"{self.student} — {self.question}"
