from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.core.access import admin_required
from apps.integrations.forms import ActiveDirectorySettingsForm, OneCIntegrationSettingsForm
from apps.integrations.models import ActiveDirectorySettings, IntegrationSyncLog, OneCIntegrationSettings
from apps.integrations.services.active_directory import (
    IntegrationConfigurationError as ActiveDirectoryIntegrationConfigurationError,
    test_active_directory_connection,
)
from apps.integrations.services.one_c import (
    IntegrationConfigurationError as OneCIntegrationConfigurationError,
    sync_one_c_data,
)

@login_required
@admin_required
def integrations_admin_view(request):
    one_c_settings = OneCIntegrationSettings.load()
    active_directory_settings = ActiveDirectorySettings.load()
    one_c_form = OneCIntegrationSettingsForm(instance=one_c_settings, prefix="onec")
    active_directory_form = ActiveDirectorySettingsForm(instance=active_directory_settings, prefix="ad")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "save_onec":
            one_c_form = OneCIntegrationSettingsForm(request.POST, instance=one_c_settings, prefix="onec")
            if one_c_form.is_valid():
                one_c_form.save()
                messages.success(request, "Настройки интеграции 1С сохранены.")
                return redirect("integrations-admin")
            messages.error(request, "Не удалось сохранить настройки 1С. Проверьте форму.")

        elif action == "save_ad":
            active_directory_form = ActiveDirectorySettingsForm(
                request.POST,
                instance=active_directory_settings,
                prefix="ad",
            )
            if active_directory_form.is_valid():
                active_directory_form.save()
                messages.success(request, "Настройки Active Directory сохранены.")
                return redirect("integrations-admin")
            messages.error(request, "Не удалось сохранить настройки Active Directory. Проверьте форму.")

        elif action == "sync_onec":
            try:
                result = sync_one_c_data(actor=request.user)
            except OneCIntegrationConfigurationError as exc:
                messages.error(request, str(exc))
            except Exception as exc:
                messages.error(request, f"Синхронизация 1С завершилась ошибкой: {exc}")
            else:
                messages.success(
                    request,
                    "Синхронизация 1С завершена: "
                    f"отделов {result['departments']}, сотрудников {result['employees']}, ТМЦ {result['assets']}.",
                )
            return redirect("integrations-admin")

        elif action == "test_ad":
            try:
                result = test_active_directory_connection(actor=request.user)
            except ActiveDirectoryIntegrationConfigurationError as exc:
                messages.error(request, str(exc))
            except Exception as exc:
                messages.error(request, f"Проверка Active Directory завершилась ошибкой: {exc}")
            else:
                messages.success(
                    request,
                    "Подключение к Active Directory проверено успешно. "
                    f"Пользователь поиска: {result['bind_identity']}.",
                )
            return redirect("integrations-admin")

    return render(
        request,
        "integrations_admin.html",
        {
            "user_data": request.user,
            "one_c_form": one_c_form,
            "active_directory_form": active_directory_form,
            "one_c_settings": one_c_settings,
            "active_directory_settings": active_directory_settings,
            "recent_logs": IntegrationSyncLog.objects.select_related("triggered_by")[:12],
        },
    )
