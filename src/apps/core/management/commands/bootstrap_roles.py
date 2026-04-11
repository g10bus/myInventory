from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    "employee": [
        "view_asset",
        "view_assetassignment",
        "view_transferrequest",
    ],
    "inventory_operator": [
        "add_asset",
        "change_asset",
        "view_asset",
        "add_assetassignment",
        "change_assetassignment",
        "view_assetassignment",
        "add_transferrequest",
        "change_transferrequest",
        "view_transferrequest",
        "view_auditevent",
    ],
    "department_manager": [
        "view_asset",
        "view_assetassignment",
        "view_transferrequest",
        "view_auditevent",
    ],
    "auditor": [
        "view_asset",
        "view_assetassignment",
        "view_transferrequest",
        "view_auditevent",
    ],
    "system_admin": [],
}


class Command(BaseCommand):
    help = "Создает базовые группы и права доступа"

    def handle(self, *args, **options):
        for group_name, codenames in ROLE_PERMISSIONS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            if codenames:
                permissions = Permission.objects.filter(codename__in=codenames)
                group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"Группа '{group_name}' готова"))

        user_model = get_user_model()
        admins = user_model.objects.filter(is_superuser=True)
        admin_group = Group.objects.get(name="system_admin")
        for admin in admins:
            admin.groups.add(admin_group)
