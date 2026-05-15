from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ActiveDirectorySettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("enabled", models.BooleanField(default=False)),
                ("server_uri", models.CharField(blank=True, max_length=255)),
                ("domain", models.CharField(blank=True, max_length=120)),
                ("base_dn", models.CharField(blank=True, max_length=255)),
                ("bind_dn", models.CharField(blank=True, max_length=255)),
                ("bind_password", models.CharField(blank=True, max_length=255)),
                ("user_search_filter", models.CharField(default="(&(objectClass=user)(|(mail={identifier})(userPrincipalName={identifier})(sAMAccountName={sam_account_name})))", max_length=255)),
                ("email_attribute", models.CharField(default="mail", max_length=100)),
                ("first_name_attribute", models.CharField(default="givenName", max_length=100)),
                ("last_name_attribute", models.CharField(default="sn", max_length=100)),
                ("middle_name_attribute", models.CharField(blank=True, default="middleName", max_length=100)),
                ("department_attribute", models.CharField(default="department", max_length=100)),
                ("title_attribute", models.CharField(default="title", max_length=100)),
                ("location_attribute", models.CharField(default="physicalDeliveryOfficeName", max_length=100)),
                ("display_name_attribute", models.CharField(default="displayName", max_length=100)),
                ("use_ssl", models.BooleanField(default=False)),
                ("timeout_seconds", models.PositiveSmallIntegerField(default=10)),
                ("sync_profile_on_login", models.BooleanField(default=True)),
                ("last_connection_check_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Настройки Active Directory",
                "verbose_name_plural": "Настройки Active Directory",
            },
        ),
        migrations.CreateModel(
            name="OneCIntegrationSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("enabled", models.BooleanField(default=False)),
                ("base_url", models.URLField(blank=True)),
                ("username", models.CharField(blank=True, max_length=150)),
                ("password", models.CharField(blank=True, max_length=255)),
                ("api_token", models.CharField(blank=True, max_length=255)),
                ("departments_endpoint", models.CharField(default="/departments", max_length=120)),
                ("employees_endpoint", models.CharField(default="/employees", max_length=120)),
                ("assets_endpoint", models.CharField(default="/assets", max_length=120)),
                ("verify_ssl", models.BooleanField(default=True)),
                ("timeout_seconds", models.PositiveSmallIntegerField(default=15)),
                ("sync_departments", models.BooleanField(default=True)),
                ("sync_employees", models.BooleanField(default=True)),
                ("sync_assets", models.BooleanField(default=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Настройки интеграции 1С",
                "verbose_name_plural": "Настройки интеграции 1С",
            },
        ),
        migrations.CreateModel(
            name="IntegrationSyncLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("integration_type", models.CharField(choices=[("one_c", "1С"), ("active_directory", "Active Directory")], max_length=32)),
                ("status", models.CharField(choices=[("running", "В процессе"), ("success", "Успешно"), ("failed", "Ошибка")], default="running", max_length=20)),
                ("action", models.CharField(blank=True, max_length=50)),
                ("message", models.TextField(blank=True)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("triggered_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="integration_logs", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Журнал интеграции",
                "verbose_name_plural": "Журнал интеграций",
                "ordering": ["-started_at", "-created_at"],
            },
        ),
    ]

