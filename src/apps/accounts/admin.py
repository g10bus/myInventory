from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "last_name",
        "first_name",
        "department",
        "position",
        "role",
        "is_active",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "department", "role")
    search_fields = ("email", "last_name", "first_name", "middle_name", "phone")
    ordering = ("email",)
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Корпоративный профиль",
            {
                "fields": (
                    "middle_name",
                    "phone",
                    "role",
                    "position",
                    "office_location",
                    "department",
                )
            },
        ),
    )
