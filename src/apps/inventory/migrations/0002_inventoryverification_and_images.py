from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="InventoryVerification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("verified_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("location", models.CharField(blank=True, max_length=150)),
                ("next_verification_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("asset", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_records", to="inventory.asset")),
                ("responsible_employee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inventory_verifications_as_responsible", to=settings.AUTH_USER_MODEL)),
                ("verified_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="inventory_verifications_completed", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Фиксация инвентаризации",
                "verbose_name_plural": "Фиксации инвентаризации",
                "ordering": ["-verified_at", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="InventoryVerificationImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.ImageField(upload_to="inventory_verifications/%Y/%m/%d/")),
                ("caption", models.CharField(blank=True, max_length=255)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("verification", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="inventory.inventoryverification")),
            ],
            options={
                "verbose_name": "Изображение инвентаризации",
                "verbose_name_plural": "Изображения инвентаризации",
                "ordering": ["sort_order", "created_at"],
            },
        ),
    ]
