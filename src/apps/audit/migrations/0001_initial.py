import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("event_type", models.CharField(choices=[("asset_issued", "Выдача ТМЦ"), ("asset_returned", "Возврат ТМЦ"), ("transfer_requested", "Запрос на передачу"), ("transfer_approved", "Передача подтверждена"), ("transfer_rejected", "Передача отклонена"), ("asset_verified", "Сверка ТМЦ"), ("asset_written_off", "Списание ТМЦ")], max_length=50)),
                ("message", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("occurred_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to="accounts.user")),
                ("asset", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to="inventory.asset")),
                ("related_user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="related_audit_events", to="accounts.user")),
            ],
            options={
                "verbose_name": "Событие аудита",
                "verbose_name_plural": "События аудита",
                "ordering": ["-occurred_at"],
            },
        ),
    ]
