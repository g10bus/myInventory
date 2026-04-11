from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "event_type", "actor", "related_user", "asset")
    search_fields = ("message", "event_type", "asset__inventory_number", "actor__email")
    list_filter = ("event_type",)
