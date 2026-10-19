from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import School, SchoolClass, TermSubscription, User


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(User)
class SchoolUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("School access", {"fields": ("role", "school", "school_class")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("School access", {"fields": ("role", "school", "school_class")}),
    )
    list_display = ("username", "first_name", "last_name", "role", "school", "school_class", "is_active")
    list_filter = ("role", "school", "school_class", "is_active")


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "school")
    list_filter = ("school",)
    search_fields = ("name", "school__name")


@admin.register(TermSubscription)
class TermSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("school", "term_name", "starts_at", "ends_at", "seat_limit", "status")
    list_filter = ("status", "school")
    search_fields = ("school__name", "term_name", "paystack_reference")
