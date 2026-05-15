from django.core.management.base import BaseCommand, CommandError

from apps.integrations.services.active_directory import (
    IntegrationConfigurationError,
    test_active_directory_connection,
)


class Command(BaseCommand):
    help = "Проверяет подключение к Active Directory."

    def handle(self, *args, **options):
        try:
            result = test_active_directory_connection()
        except IntegrationConfigurationError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Подключение к Active Directory выполнено успешно. "
                f"Учетная запись поиска: {result['bind_identity']}."
            )
        )

