from django.contrib import admin

from .models import ActiveDirectorySettings, IntegrationSyncLog, OneCIntegrationSettings


@admin.register(OneCIntegrationSettings)
class OneCIntegrationSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "enabled", "base_url", "last_synced_at")


@admin.register(ActiveDirectorySettings)
class ActiveDirectorySettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "enabled", "server_uri", "domain", "last_connection_check_at")


@admin.register(IntegrationSyncLog)
class IntegrationSyncLogAdmin(admin.ModelAdmin):
    list_display = ("integration_type", "action", "status", "triggered_by", "started_at", "finished_at")
    list_filter = ("integration_type", "status", "action")
    search_fields = ("message",)

