from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class SingletonSettingsMixin:
    @classmethod
    def load(cls):
        instance = cls.objects.order_by("pk").first()
        return instance or cls()


class OneCIntegrationSettings(SingletonSettingsMixin, TimeStampedModel):
    enabled = models.BooleanField(default=False)
    base_url = models.URLField(blank=True)
    username = models.CharField(max_length=150, blank=True)
    password = models.CharField(max_length=255, blank=True)
    api_token = models.CharField(max_length=255, blank=True)
    departments_endpoint = models.CharField(max_length=120, default="/departments")
    employees_endpoint = models.CharField(max_length=120, default="/employees")
    assets_endpoint = models.CharField(max_length=120, default="/assets")
    verify_ssl = models.BooleanField(default=True)
    timeout_seconds = models.PositiveSmallIntegerField(default=15)
    sync_departments = models.BooleanField(default=True)
    sync_employees = models.BooleanField(default=True)
    sync_assets = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Настройки интеграции 1С"
        verbose_name_plural = "Настройки интеграции 1С"

    def __str__(self):
        return "Интеграция 1С"


class ActiveDirectorySettings(SingletonSettingsMixin, TimeStampedModel):
    enabled = models.BooleanField(default=False)
    server_uri = models.CharField(max_length=255, blank=True)
    domain = models.CharField(max_length=120, blank=True)
    base_dn = models.CharField(max_length=255, blank=True)
    bind_dn = models.CharField(max_length=255, blank=True)
    bind_password = models.CharField(max_length=255, blank=True)
    user_search_filter = models.CharField(
        max_length=255,
        default="(&(objectClass=user)(|(mail={identifier})(userPrincipalName={identifier})(sAMAccountName={sam_account_name})))",
    )
    email_attribute = models.CharField(max_length=100, default="mail")
    first_name_attribute = models.CharField(max_length=100, default="givenName")
    last_name_attribute = models.CharField(max_length=100, default="sn")
    middle_name_attribute = models.CharField(max_length=100, blank=True, default="middleName")
    department_attribute = models.CharField(max_length=100, default="department")
    title_attribute = models.CharField(max_length=100, default="title")
    location_attribute = models.CharField(max_length=100, default="physicalDeliveryOfficeName")
    display_name_attribute = models.CharField(max_length=100, default="displayName")
    use_ssl = models.BooleanField(default=False)
    timeout_seconds = models.PositiveSmallIntegerField(default=10)
    sync_profile_on_login = models.BooleanField(default=True)
    last_connection_check_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Настройки Active Directory"
        verbose_name_plural = "Настройки Active Directory"

    def __str__(self):
        return "Интеграция Active Directory"

    def render_search_filter(self, identifier):
        safe_identifier = _escape_ldap_filter_value(identifier)
        sam_account_name = _escape_ldap_filter_value(identifier.split("@", 1)[0].split("\\")[-1])
        return self.user_search_filter.format(
            identifier=safe_identifier,
            sam_account_name=sam_account_name,
        )


def _escape_ldap_filter_value(value):
    normalized = str(value or "")
    return (
        normalized.replace("\\", r"\5c")
        .replace("*", r"\2a")
        .replace("(", r"\28")
        .replace(")", r"\29")
        .replace("\x00", r"\00")
    )


class IntegrationSyncLog(TimeStampedModel):
    class IntegrationType(models.TextChoices):
        ONE_C = "one_c", "1С"
        ACTIVE_DIRECTORY = "active_directory", "Active Directory"

    class Status(models.TextChoices):
        RUNNING = "running", "В процессе"
        SUCCESS = "success", "Успешно"
        FAILED = "failed", "Ошибка"

    integration_type = models.CharField(max_length=32, choices=IntegrationType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    action = models.CharField(max_length=50, blank=True)
    message = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="integration_logs",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Журнал интеграции"
        verbose_name_plural = "Журнал интеграций"
        ordering = ["-started_at", "-created_at"]

    def __str__(self):
        return f"{self.get_integration_type_display()} - {self.get_status_display()}"
