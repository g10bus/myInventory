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
            name="AssetAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assigned_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("returned_at", models.DateTimeField(blank=True, null=True)),
                ("location_at_issue", models.CharField(blank=True, max_length=150)),
                ("note", models.TextField(blank=True)),
                ("is_current", models.BooleanField(default=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="inventory.asset")),
                ("assigned_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="issued_assets", to="accounts.user")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="asset_assignments", to="accounts.user")),
            ],
            options={
                "verbose_name": "Закрепление ТМЦ",
                "verbose_name_plural": "Закрепления ТМЦ",
                "ordering": ["-assigned_at"],
            },
        ),
        migrations.CreateModel(
            name="TransferRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("pending", "На согласовании"), ("rejected", "Отклонена"), ("completed", "Завершена")], default="pending", max_length=20)),
                ("comment", models.TextField(blank=True)),
                ("requested_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="transfer_requests", to="inventory.asset")),
                ("from_employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outgoing_transfer_requests", to="accounts.user")),
                ("processed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="processed_transfer_requests", to="accounts.user")),
                ("to_employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incoming_transfer_requests", to="accounts.user")),
            ],
            options={
                "verbose_name": "Запрос на передачу",
                "verbose_name_plural": "Запросы на передачу",
                "ordering": ["-requested_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="assetassignment",
            constraint=models.UniqueConstraint(condition=models.Q(("is_current", True)), fields=("asset",), name="unique_current_asset_assignment"),
        ),
    ]
