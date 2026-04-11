from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Asset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("category", models.CharField(max_length=120)),
                ("title", models.CharField(max_length=150)),
                ("model_name", models.CharField(blank=True, max_length=150)),
                ("inventory_number", models.CharField(max_length=50, unique=True)),
                ("serial_number", models.CharField(blank=True, max_length=80)),
                ("status", models.CharField(choices=[("in_use", "В эксплуатации"), ("repair", "В ремонте"), ("broken", "Требует списания"), ("reserve", "В резерве")], default="in_use", max_length=20)),
                ("location", models.CharField(blank=True, max_length=150)),
                ("last_verified_at", models.DateField(blank=True, null=True)),
                ("next_verification_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "ТМЦ",
                "verbose_name_plural": "ТМЦ",
                "ordering": ["category", "title", "inventory_number"],
            },
        ),
    ]
