from django.contrib import admin

from .models import AssetAssignment, TransferRequest


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = ("asset", "employee", "assigned_at", "returned_at", "is_current")
    list_filter = ("is_current", "employee__department")
    search_fields = ("asset__inventory_number", "asset__title", "employee__email")


@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    list_display = ("asset", "from_employee", "to_employee", "status", "requested_at")
    list_filter = ("status",)
    search_fields = (
        "asset__inventory_number",
        "asset__title",
        "from_employee__email",
        "to_employee__email",
    )
