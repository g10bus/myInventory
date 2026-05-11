from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_employeeinventoryassignment"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="employeeinventoryassignment",
            name="revocation_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="employeeinventoryassignment",
            name="revoked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="employeeinventoryassignment",
            name="revoked_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="inventory_assignments_revoked",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
