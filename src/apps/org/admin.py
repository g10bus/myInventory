from django.contrib import admin

from .models import Department, Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "address")
    search_fields = ("name", "code", "address")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "location")
    search_fields = ("name", "code", "location")
