from django.contrib import admin

from .models import Asset, InventoryVerification, InventoryVerificationImage


class InventoryVerificationImageInline(admin.TabularInline):
    model = InventoryVerificationImage
    extra = 1
    fields = ("image", "caption", "sort_order")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        "inventory_number",
        "title",
        "category",
        "status",
        "location",
        "next_verification_date",
    )
    list_filter = ("category", "status")
    search_fields = ("inventory_number", "title", "model_name", "serial_number")


@admin.register(InventoryVerification)
class InventoryVerificationAdmin(admin.ModelAdmin):
    list_display = (
        "asset",
        "verified_at",
        "verified_by",
        "responsible_employee",
        "location",
        "next_verification_date",
    )
    list_filter = ("verified_at", "next_verification_date")
    search_fields = (
        "asset__inventory_number",
        "asset__title",
        "location",
        "notes",
        "verified_by__email",
        "responsible_employee__email",
    )
    autocomplete_fields = ("asset", "verified_by", "responsible_employee")
    inlines = [InventoryVerificationImageInline]


@admin.register(InventoryVerificationImage)
class InventoryVerificationImageAdmin(admin.ModelAdmin):
    list_display = ("verification", "caption", "sort_order", "created_at")
    list_filter = ("created_at",)
    search_fields = ("verification__asset__inventory_number", "caption")
    autocomplete_fields = ("verification",)
