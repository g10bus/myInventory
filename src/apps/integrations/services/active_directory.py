from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import log_event
from apps.integrations.models import ActiveDirectorySettings, IntegrationSyncLog
from apps.integrations.services.logging import finish_log, start_log
from apps.org.models import Department, Location


class IntegrationConfigurationError(Exception):
    pass


def _load_ldap3():
    try:
        import ldap3
    except ImportError as exc:
        raise IntegrationConfigurationError("Для интеграции Active Directory требуется установить пакет ldap3.") from exc
    return ldap3


def _looks_like_email(value):
    return isinstance(value, str) and "@" in value and "." in value.rsplit("@", 1)[-1]


def _build_bind_identity(identifier, settings_obj):
    normalized = str(identifier or "").strip()
    if not normalized:
        return normalized
    if "\\" in normalized or "@" in normalized or not settings_obj.domain:
        return normalized
    return f"{settings_obj.domain}\\{normalized}"


def _get_entry_attribute(entry, attribute_name):
    if not entry or not attribute_name:
        return ""
    if isinstance(entry, dict):
        value = entry.get(attribute_name)
        if isinstance(value, dict) and "value" in value:
            return value.get("value") or ""
        return value or ""
    try:
        value = entry[attribute_name].value
    except Exception:
        try:
            value = getattr(entry, attribute_name).value
        except Exception:
            return ""
    if isinstance(value, list):
        return value[0] if value else ""
    return value or ""


def _build_attribute_list(settings_obj):
    return [
        field_name
        for field_name in {
            settings_obj.email_attribute,
            settings_obj.first_name_attribute,
            settings_obj.last_name_attribute,
            settings_obj.middle_name_attribute,
            settings_obj.department_attribute,
            settings_obj.title_attribute,
            settings_obj.location_attribute,
            settings_obj.display_name_attribute,
        }
        if field_name
    ]


def _find_directory_entry(connection, settings_obj, identifier):
    if not settings_obj.base_dn:
        return None
    attributes = _build_attribute_list(settings_obj)
    search_filter = settings_obj.render_search_filter(identifier)
    connection.search(settings_obj.base_dn, search_filter, attributes=attributes)
    return connection.entries[0] if connection.entries else None


def _split_display_name(display_name):
    parts = [part for part in str(display_name or "").split() if part]
    last_name = parts[0] if len(parts) > 0 else ""
    first_name = parts[1] if len(parts) > 1 else ""
    middle_name = parts[2] if len(parts) > 2 else ""
    return last_name, first_name, middle_name


def _sync_local_user(identifier, entry, settings_obj):
    email = str(_get_entry_attribute(entry, settings_obj.email_attribute) or "").strip().lower()
    if not email and _looks_like_email(identifier):
        email = identifier.lower()
    if not email:
        account_name = str(identifier).split("\\")[-1].split("@")[0]
        domain_suffix = settings_obj.domain.lower() if settings_obj.domain else "local"
        email = f"{account_name}@{domain_suffix}"

    user = User.objects.filter(email__iexact=email).first() or User.objects.filter(username__iexact=email).first()
    if user is None:
        user = User(email=email, username=email)
        user.set_unusable_password()

    first_name = _get_entry_attribute(entry, settings_obj.first_name_attribute)
    last_name = _get_entry_attribute(entry, settings_obj.last_name_attribute)
    middle_name = _get_entry_attribute(entry, settings_obj.middle_name_attribute)
    if not (first_name or last_name):
        last_name, first_name, middle_name = _split_display_name(
            _get_entry_attribute(entry, settings_obj.display_name_attribute)
        )

    department_name = _get_entry_attribute(entry, settings_obj.department_attribute)
    location_name = _get_entry_attribute(entry, settings_obj.location_attribute)
    department = None
    if department_name:
        if location_name:
            Location.objects.get_or_create(name=location_name)
        department, _ = Department.objects.get_or_create(
            name=department_name,
            defaults={"location": location_name},
        )

    user.email = email
    user.username = email
    user.first_name = first_name
    user.last_name = last_name
    user.middle_name = middle_name
    user.position = _get_entry_attribute(entry, settings_obj.title_attribute)
    user.office_location = location_name
    user.department = department
    user.role = user.role or "Сотрудник"
    user.save()
    return user


def authenticate_with_active_directory(identifier, password):
    settings_obj = ActiveDirectorySettings.load()
    if not settings_obj.pk or not settings_obj.enabled:
        return None
    if not identifier or not password:
        return None
    if not settings_obj.server_uri or not settings_obj.base_dn:
        return None

    ldap3 = _load_ldap3()
    server = ldap3.Server(
        settings_obj.server_uri,
        use_ssl=settings_obj.use_ssl,
        connect_timeout=settings_obj.timeout_seconds,
        get_info=ldap3.NONE,
    )
    bind_identity = _build_bind_identity(identifier, settings_obj)
    connection = ldap3.Connection(
        server,
        user=bind_identity,
        password=password,
        auto_bind=True,
        receive_timeout=settings_obj.timeout_seconds,
    )

    entry = None
    if settings_obj.sync_profile_on_login:
        entry = _find_directory_entry(connection, settings_obj, identifier)
    user = _sync_local_user(identifier, entry or {}, settings_obj)
    if not user.is_active:
        return None
    return user


def test_active_directory_connection(*, actor=None):
    settings_obj = ActiveDirectorySettings.load()
    if not settings_obj.pk or not settings_obj.enabled:
        raise IntegrationConfigurationError("Интеграция Active Directory не включена. Сначала сохраните и активируйте настройки.")
    if not settings_obj.server_uri or not settings_obj.base_dn:
        raise IntegrationConfigurationError("Для Active Directory укажите сервер и base DN.")
    if not settings_obj.bind_dn or not settings_obj.bind_password:
        raise IntegrationConfigurationError("Для проверки подключения укажите bind DN и пароль учетной записи поиска.")

    log = start_log(
        integration_type=IntegrationSyncLog.IntegrationType.ACTIVE_DIRECTORY,
        action="connection_test",
        triggered_by=actor,
    )

    ldap3 = _load_ldap3()
    try:
        server = ldap3.Server(
            settings_obj.server_uri,
            use_ssl=settings_obj.use_ssl,
            connect_timeout=settings_obj.timeout_seconds,
            get_info=ldap3.NONE,
        )
        ldap3.Connection(
            server,
            user=settings_obj.bind_dn,
            password=settings_obj.bind_password,
            auto_bind=True,
            receive_timeout=settings_obj.timeout_seconds,
        )
    except Exception as exc:
        finish_log(
            log,
            status=IntegrationSyncLog.Status.FAILED,
            message=f"Ошибка проверки Active Directory: {exc}",
            details={},
        )
        raise

    settings_obj.last_connection_check_at = timezone.now()
    settings_obj.save(update_fields=["last_connection_check_at", "updated_at"])
    finish_log(
        log,
        status=IntegrationSyncLog.Status.SUCCESS,
        message="Подключение к Active Directory подтверждено.",
        details={"bind_identity": settings_obj.bind_dn},
    )
    log_event(
        event_type="integration_active_directory_check",
        actor=actor,
        message="Проверено подключение к Active Directory.",
        metadata={"bind_identity": settings_obj.bind_dn},
    )
    return {"bind_identity": settings_obj.bind_dn}

