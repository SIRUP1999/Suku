from django.contrib import admin

from .models import Attempt, Question, Subject, Topic


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 0


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ("kind", "prompt", "difficulty", "is_published")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_published", "position")
    list_filter = ("is_published",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = (TopicInline,)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "subject", "is_published", "position")
    list_filter = ("subject", "grade", "term", "is_published")
    search_fields = ("title", "subject__name")
    inlines = (QuestionInline,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "kind", "difficulty", "is_published")
    list_filter = ("kind", "difficulty", "is_published", "topic__subject")
    search_fields = ("prompt", "topic__title")


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "school", "question", "is_correct", "score", "created_at")
    list_filter = ("school", "is_correct", "question__topic__subject")
    search_fields = ("student__username", "question__prompt")
    readonly_fields = ("created_at",)
