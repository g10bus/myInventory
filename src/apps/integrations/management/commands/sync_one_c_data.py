from django.core.management.base import BaseCommand, CommandError

from apps.integrations.services.one_c import IntegrationConfigurationError, sync_one_c_data


class Command(BaseCommand):
    help = "Запускает синхронизацию данных из 1С."

    def handle(self, *args, **options):
        try:
            result = sync_one_c_data()
        except IntegrationConfigurationError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Синхронизация 1С завершена: "
                f"отделов {result['departments']}, "
                f"сотрудников {result['employees']}, "
                f"ТМЦ {result['assets']}."
            )
        )

