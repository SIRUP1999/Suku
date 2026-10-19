from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class School(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def has_current_subscription(self):
        return self.subscriptions.filter(
            status=TermSubscription.Status.ACTIVE,
            starts_at__lte=timezone.now().date(),
            ends_at__gte=timezone.now().date(),
        ).exists()


class SchoolClass(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(fields=("school", "name"), name="unique_class_name_per_school")
        ]

    def __str__(self):
        return f"{self.school} — {self.name}"


class User(AbstractUser):
    class Role(models.TextChoices):
        SCHOOL_ADMIN = "school_admin", "School Admin"
        STUDENT = "student", "Student"
        TEACHER = "teacher", "Teacher"

    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.SCHOOL_ADMIN
    )
    school = models.ForeignKey(
        School, on_delete=models.PROTECT, related_name="users", null=True, blank=True
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        related_name="students",
        null=True,
        blank=True,
    )

    def clean(self):
        super().clean()
        if self.role in (self.Role.SCHOOL_ADMIN, self.Role.STUDENT) and not self.school_id:
            from django.core.exceptions import ValidationError

            raise ValidationError({"school": "School admins and students must belong to a school."})
        if self.school_class_id and self.school_class.school_id != self.school_id:
            from django.core.exceptions import ValidationError

            raise ValidationError({"school_class": "Student class must belong to the same school."})
        if self.school_class_id and self.role != self.Role.STUDENT:
            from django.core.exceptions import ValidationError

            raise ValidationError({"school_class": "Only students can be assigned to a class."})


class TermSubscription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="subscriptions")
    term_name = models.CharField(max_length=100)
    starts_at = models.DateField()
    ends_at = models.DateField()
    seat_limit = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    paystack_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(ends_at__gte=models.F("starts_at")), name="subscription_dates_valid"),
            models.CheckConstraint(condition=models.Q(seat_limit__gt=0), name="subscription_has_seats"),
        ]

    def __str__(self):
        return f"{self.school} — {self.term_name}"

    @property
    def is_current(self):
        today = timezone.now().date()
        return self.status == self.Status.ACTIVE and self.starts_at <= today <= self.ends_at
