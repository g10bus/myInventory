from urllib.parse import urljoin

from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import log_event
from apps.integrations.models import IntegrationSyncLog, OneCIntegrationSettings
from apps.integrations.services.logging import finish_log, start_log
from apps.inventory.models import Asset
from apps.org.models import Department, Location


class IntegrationConfigurationError(Exception):
    pass


def _load_requests():
    try:
        import requests
    except ImportError as exc:
        raise IntegrationConfigurationError("Для интеграции 1С требуется установить пакет requests.") from exc
    return requests


def _normalize_collection(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "results", "data", "value"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def _pick(item, *keys, default=""):
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return default


def _looks_like_email(value):
    return isinstance(value, str) and "@" in value and "." in value.rsplit("@", 1)[-1]


def _normalize_status(value):
    normalized = str(value or "").strip().lower()
    mapping = {
        "in_use": Asset.Status.IN_USE,
        "issued": Asset.Status.IN_USE,
        "active": Asset.Status.IN_USE,
        "repair": Asset.Status.REPAIR,
        "service": Asset.Status.REPAIR,
        "broken": Asset.Status.BROKEN,
        "write_off": Asset.Status.BROKEN,
        "reserve": Asset.Status.RESERVE,
        "stock": Asset.Status.RESERVE,
    }
    return mapping.get(normalized, Asset.Status.RESERVE)


class OneCClient:
    def __init__(self, settings_obj):
        requests = _load_requests()
        self.settings = settings_obj
        self.session = requests.Session()
        if settings_obj.api_token:
            self.session.headers.update({"Authorization": f"Bearer {settings_obj.api_token}"})
        if settings_obj.username and settings_obj.password:
            self.session.auth = (settings_obj.username, settings_obj.password)

    def get_json(self, endpoint):
        url = urljoin(f"{self.settings.base_url.rstrip('/')}/", endpoint.lstrip("/"))
        response = self.session.get(
            url,
            timeout=self.settings.timeout_seconds,
            verify=self.settings.verify_ssl,
        )
        response.raise_for_status()
        return response.json()


def _sync_departments(items):
    created_or_updated = 0
    for item in items:
        name = _pick(item, "name", "department_name")
        if not name:
            continue
        location_name = _pick(item, "location", "location_name")
        if location_name:
            Location.objects.get_or_create(name=location_name)
        Department.objects.update_or_create(
            name=name,
            defaults={
                "code": _pick(item, "code", "department_code"),
                "location": location_name,
            },
        )
        created_or_updated += 1
    return created_or_updated


def _sync_employees(items):
    created_or_updated = 0
    skipped = 0
    for item in items:
        email = str(_pick(item, "email", "work_email")).strip().lower()
        login = str(_pick(item, "login", "username")).strip()
        if not email:
            if _looks_like_email(login):
                email = login.lower()
            else:
                skipped += 1
                continue

        department_name = _pick(item, "department", "department_name")
        department = None
        if department_name:
            department, _ = Department.objects.get_or_create(
                name=department_name,
                defaults={
                    "code": _pick(item, "department_code"),
                    "location": _pick(item, "location", "office_location"),
                },
            )

        location_name = _pick(item, "location", "office_location")
        if location_name:
            Location.objects.get_or_create(name=location_name)

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={"username": email},
        )
        user.username = email
        user.first_name = _pick(item, "first_name", "name")
        user.last_name = _pick(item, "last_name", "surname")
        user.middle_name = _pick(item, "middle_name", "patronymic")
        user.phone = _pick(item, "phone", "mobile_phone")
        user.position = _pick(item, "position", "job_title")
        user.role = _pick(item, "role", default=user.role or "Сотрудник")
        user.office_location = location_name
        user.department = department
        if not user.password:
            user.set_unusable_password()
        user.save()
        created_or_updated += 1
    return created_or_updated, skipped


def _sync_assets(items):
    created_or_updated = 0
    skipped = 0
    for item in items:
        inventory_number = str(_pick(item, "inventory_number", "inventoryNumber", "code")).strip()
        if not inventory_number:
            skipped += 1
            continue

        Asset.objects.update_or_create(
            inventory_number=inventory_number,
            defaults={
                "category": _pick(item, "category", default="ТМЦ"),
                "title": _pick(item, "title", "name", default=inventory_number),
                "model_name": _pick(item, "model_name", "model"),
                "serial_number": _pick(item, "serial_number", "serial"),
                "status": _normalize_status(_pick(item, "status", "state")),
                "location": _pick(item, "location", "warehouse", "office_location"),
                "notes": _pick(item, "notes", "comment"),
            },
        )
        created_or_updated += 1
    return created_or_updated, skipped


def sync_one_c_data(*, actor=None):
    settings_obj = OneCIntegrationSettings.load()
    if not settings_obj.pk or not settings_obj.enabled:
        raise IntegrationConfigurationError("Интеграция 1С не включена. Сначала сохраните и активируйте настройки.")
    if not settings_obj.base_url:
        raise IntegrationConfigurationError("Для синхронизации 1С укажите базовый URL.")

    log = start_log(
        integration_type=IntegrationSyncLog.IntegrationType.ONE_C,
        action="sync",
        triggered_by=actor,
    )
    result = {
        "departments": 0,
        "employees": 0,
        "employees_skipped": 0,
        "assets": 0,
        "assets_skipped": 0,
    }
    client = OneCClient(settings_obj)

    try:
        if settings_obj.sync_departments and settings_obj.departments_endpoint:
            result["departments"] = _sync_departments(
                _normalize_collection(client.get_json(settings_obj.departments_endpoint))
            )
        if settings_obj.sync_employees and settings_obj.employees_endpoint:
            employees, employees_skipped = _sync_employees(
                _normalize_collection(client.get_json(settings_obj.employees_endpoint))
            )
            result["employees"] = employees
            result["employees_skipped"] = employees_skipped
        if settings_obj.sync_assets and settings_obj.assets_endpoint:
            assets, assets_skipped = _sync_assets(
                _normalize_collection(client.get_json(settings_obj.assets_endpoint))
            )
            result["assets"] = assets
            result["assets_skipped"] = assets_skipped
    except Exception as exc:
        finish_log(
            log,
            status=IntegrationSyncLog.Status.FAILED,
            message=f"Ошибка синхронизации 1С: {exc}",
            details=result,
        )
        raise

    settings_obj.last_synced_at = timezone.now()
    settings_obj.save(update_fields=["last_synced_at", "updated_at"])
    finish_log(
        log,
        status=IntegrationSyncLog.Status.SUCCESS,
        message="Синхронизация 1С завершена успешно.",
        details=result,
    )
    log_event(
        event_type="integration_one_c_sync",
        actor=actor,
        message="Выполнена синхронизация данных из 1С.",
        metadata=result,
    )
    return result

