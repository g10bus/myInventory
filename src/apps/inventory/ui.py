from datetime import date

from django.db.models import Exists, OuterRef
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.inventory.models import InventoryVerification

from .selectors import get_active_inventory_assignment, get_user_inventory_assignments


def build_verification_records(asset):
    current_assignment = asset.current_assignment
    verification_records = (
        asset.verification_records.select_related("verified_by", "responsible_employee")
        .prefetch_related("images")
        .order_by("-verified_at", "-created_at")[:5]
    )
    records = [
        _build_verification_record_from_model(
            verification=verification,
            asset=asset,
            current_assignment=current_assignment,
        )
        for verification in verification_records
    ]

    if records:
        return records

    verification_events = (
        asset.audit_events.filter(event_type=AuditEvent.EventType.ASSET_VERIFIED)
        .select_related("actor", "related_user")
        .order_by("-occurred_at")[:5]
    )
    records = [
        _build_verification_record_from_event(
            event=event,
            asset=asset,
            current_assignment=current_assignment,
        )
        for event in verification_events
    ]

    if not records and asset.last_verified_at:
        records.append(
            {
                "occurred_at": asset.last_verified_at,
                "verified_by": "Не указан",
                "responsible_person": _resolve_responsible_person(None, current_assignment),
                "location": asset.location,
                "next_verification_date": asset.next_verification_date,
                "message": "Данная запись создана автоматически.",
                "image_url": "",
                "image_caption": "",
                "images_count": 0,
            }
        )

    return records


def build_verification_form_initial(asset):
    location = asset.location
    if not location and asset.current_assignment:
        location = asset.current_assignment.location_at_issue

    return {"location": location}


def resolve_inventory_window(user):
    today = timezone.localdate()
    assignments = get_user_inventory_assignments(user)
    active_assignment = get_active_inventory_assignment(user, on_date=today)

    if not assignments.exists():
        return {
            "verification_allowed": False,
            "active_inventory_assignment": None,
            "verification_lock_message": (
                "Инвентаризация пока не назначена администратором. "
                "Проведение сверки откроется только в утвержденный период."
            ),
            "upcoming_inventory_assignment": None,
        }

    upcoming_assignment = assignments.filter(date_from__gt=today).first()
    if active_assignment:
        return {
            "verification_allowed": True,
            "active_inventory_assignment": active_assignment,
            "verification_lock_message": "",
            "upcoming_inventory_assignment": upcoming_assignment,
        }

    if upcoming_assignment:
        lock_message = (
            f"Инвентаризация будет доступна с {upcoming_assignment.date_from:%d.%m.%Y} "
            f"по {upcoming_assignment.date_to:%d.%m.%Y}."
        )
    else:
        last_assignment = assignments.filter(date_to__lt=today).order_by("-date_to").first()
        if last_assignment:
            lock_message = (
                f"Назначенный период инвентаризации завершился {last_assignment.date_to:%d.%m.%Y}. "
                "Дождитесь нового назначения администратора."
            )
        else:
            lock_message = "Проведение инвентаризации сейчас недоступно."

    return {
        "verification_allowed": False,
        "active_inventory_assignment": None,
        "verification_lock_message": lock_message,
        "upcoming_inventory_assignment": upcoming_assignment,
    }


def annotate_inventory_verification_status(assets, *, user, active_assignment):
    if not active_assignment:
        return assets

    verification_subquery = InventoryVerification.objects.filter(
        asset=OuterRef("pk"),
        responsible_employee=user,
        verified_at__date__gte=active_assignment.date_from,
        verified_at__date__lte=active_assignment.date_to,
    )

    return assets.annotate(
        has_inventory_verification_in_period=Exists(verification_subquery),
    )


def _build_verification_record_from_model(*, verification, asset, current_assignment):
    images = list(verification.images.all())
    primary_image = images[0] if images else None
    return {
        "occurred_at": verification.verified_at,
        "verified_by": verification.verified_by.full_name if verification.verified_by else "Не указан",
        "responsible_person": _resolve_responsible_person(
            verification.responsible_employee,
            current_assignment,
        ),
        "location": verification.location or asset.location,
        "next_verification_date": verification.next_verification_date,
        "message": verification.notes or "Комментарий к фиксации не добавлен.",
        "image_url": primary_image.image.url if primary_image else "",
        "image_caption": primary_image.caption if primary_image else "",
        "images_count": len(images),
    }


def _build_verification_record_from_event(*, event, asset, current_assignment):
    metadata = event.metadata if isinstance(event.metadata, dict) else {}
    next_verification_date = _parse_optional_date(metadata.get("next_verification_date"))
    location = metadata.get("location") or asset.location

    if not location and current_assignment:
        location = current_assignment.location_at_issue

    return {
        "occurred_at": event.occurred_at,
        "verified_by": event.actor.full_name if event.actor else "Не указан",
        "responsible_person": _resolve_responsible_person(event.related_user, current_assignment),
        "location": location,
        "next_verification_date": next_verification_date,
        "message": event.message,
        "image_url": "",
        "image_caption": "",
        "images_count": 0,
    }


def _resolve_responsible_person(user, current_assignment):
    if user:
        return user.full_name
    if current_assignment:
        return current_assignment.employee.full_name
    return "Не назначен"


def _parse_optional_date(value):
    if not value:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
