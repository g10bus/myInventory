from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=150, unique=True)),
                ("code", models.CharField(blank=True, max_length=30)),
                ("location", models.CharField(blank=True, max_length=150)),
            ],
            options={
                "verbose_name": "Отдел",
                "verbose_name_plural": "Отделы",
                "ordering": ["name"],
            },
        ),
    ]
