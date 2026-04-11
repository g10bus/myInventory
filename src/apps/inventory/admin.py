from django.contrib import admin

from .models import Asset


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
