from django.utils import timezone

from apps.audit.services import log_event
from apps.inventory.models import Asset


def create_asset(*, actor, data):
    asset = Asset.objects.create(**data)
    log_event(
        event_type="asset_updated",
        actor=actor,
        asset=asset,
        message=f"Создана карточка ТМЦ '{asset.title}'.",
        metadata={"created": True},
    )
    return asset


def record_verification(*, asset, actor, next_verification_date=None, note=""):
    asset.last_verified_at = timezone.localdate()
    asset.next_verification_date = next_verification_date
    asset.save(update_fields=["last_verified_at", "next_verification_date", "updated_at"])
    log_event(
        event_type="asset_verified",
        actor=actor,
        related_user=asset.assignments.filter(is_current=True).first().employee if asset.assignments.filter(is_current=True).exists() else None,
        asset=asset,
        message=note or f"Для ТМЦ '{asset.title}' зафиксирована сверка.",
        metadata={"next_verification_date": str(next_verification_date) if next_verification_date else ""},
    )
    return asset


def write_off_asset(*, asset, actor, note=""):
    asset.status = Asset.Status.BROKEN
    asset.save(update_fields=["status", "updated_at"])
    log_event(
        event_type="asset_written_off",
        actor=actor,
        asset=asset,
        message=note or f"ТМЦ '{asset.title}' переведено в статус списания.",
        metadata={},
    )
    return asset


def update_asset_details(*, asset, actor, data):
    changed_fields = []

    for field, value in data.items():
        if getattr(asset, field) != value:
            setattr(asset, field, value)
            changed_fields.append(field)

    if not changed_fields:
        return asset, changed_fields

    asset.save(update_fields=[*changed_fields, "updated_at"])
    log_event(
        event_type="asset_updated",
        actor=actor,
        asset=asset,
        message=f"Карточка ТМЦ '{asset.title}' обновлена администратором.",
        metadata={"changed_fields": changed_fields},
    )
    return asset, changed_fields
