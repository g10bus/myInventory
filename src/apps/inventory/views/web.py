from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.models import AuditEvent
from apps.inventory.forms import AssetAdminForm
from apps.inventory.models import Asset
from apps.inventory.services import create_asset, update_asset_details

from ..selectors import get_all_assets, get_user_assets


def ensure_administrator(user):
    if not user.is_administrator:
        raise PermissionDenied("Доступ разрешен только администраторам.")


def build_verification_records(asset):
    current_assignment = asset.current_assignment
    records = []

    verification_records = (
        asset.verification_records.select_related("verified_by", "responsible_employee")
        .prefetch_related("images")
        .order_by("-verified_at", "-created_at")[:5]
    )

    for verification in verification_records:
        primary_image = verification.images.first()
        records.append(
            {
                "occurred_at": verification.verified_at,
                "verified_by": verification.verified_by.full_name if verification.verified_by else "Не указан",
                "responsible_person": (
                    verification.responsible_employee.full_name
                    if verification.responsible_employee
                    else current_assignment.employee.full_name
                    if current_assignment
                    else "Не назначен"
                ),
                "location": verification.location or asset.location,
                "next_verification_date": verification.next_verification_date,
                "message": verification.notes or "Комментарий к фиксации не добавлен.",
                "image_url": primary_image.image.url if primary_image else "",
                "image_caption": primary_image.caption if primary_image else "",
                "images_count": verification.images.count(),
            }
        )

    if records:
        return records

    verification_events = (
        asset.audit_events.filter(event_type=AuditEvent.EventType.ASSET_VERIFIED)
        .select_related("actor", "related_user")
        .order_by("-occurred_at")[:5]
    )

    for event in verification_events:
        metadata = event.metadata if isinstance(event.metadata, dict) else {}
        next_verification_date = None
        raw_next_verification_date = metadata.get("next_verification_date")

        if raw_next_verification_date:
            try:
                next_verification_date = date.fromisoformat(raw_next_verification_date)
            except ValueError:
                next_verification_date = None

        location = asset.location
        if not location and current_assignment:
            location = current_assignment.location_at_issue

        records.append(
            {
                "occurred_at": event.occurred_at,
                "verified_by": event.actor.full_name if event.actor else "Не указан",
                "responsible_person": (
                    event.related_user.full_name
                    if event.related_user
                    else current_assignment.employee.full_name
                    if current_assignment
                    else "Не назначен"
                ),
                "location": location,
                "next_verification_date": next_verification_date,
                "message": event.message,
                "image_url": "",
                "image_caption": "",
                "images_count": 0,
            }
        )

    if not records and asset.last_verified_at:
        records.append(
            {
                "occurred_at": asset.last_verified_at,
                "verified_by": "Не указан",
                "responsible_person": (
                    current_assignment.employee.full_name if current_assignment else "Не назначен"
                ),
                "location": asset.location,
                "next_verification_date": asset.next_verification_date,
                "message": "Данная запись создана автоматически.",
                "image_url": "",
                "image_caption": "",
                "images_count": 0,
            }
        )

    return records


@login_required
def my_assets_view(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    assets = get_user_assets(request.user, query=query, status=status)
    return render(
        request,
        "tmc.html",
        {
            "user_data": request.user,
            "assets": assets,
            "query": query,
            "selected_status": status,
            "status_choices": Asset.Status.choices,
        },
    )


@login_required
def my_asset_detail_view(request, inventory_number):
    asset = get_object_or_404(
        get_user_assets(request.user),
        inventory_number=inventory_number,
    )
    current_assignment = asset.current_assignment
    return render(
        request,
        "tmc_detail.html",
        {
            "user_data": request.user,
            "asset": asset,
            "current_assignment": current_assignment,
            "verification_records": build_verification_records(asset),
        },
    )


@login_required
def asset_admin_view(request):
    ensure_administrator(request.user)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    assets = get_all_assets(query=query, status=status)
    return render(
        request,
        "inventory_admin.html",
        {
            "user_data": request.user,
            "assets": assets,
            "query": query,
            "selected_status": status,
            "status_choices": Asset.Status.choices,
        },
    )


@login_required
def asset_create_view(request):
    ensure_administrator(request.user)
    form = AssetAdminForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            asset = create_asset(actor=request.user, data=form.cleaned_data)
            messages.success(request, "Карточка оборудования создана.")
            return redirect("asset-edit", asset_id=asset.id)
        messages.error(request, "Не удалось создать карточку оборудования. Проверьте форму.")

    return render(
        request,
        "inventory_create.html",
        {
            "user_data": request.user,
            "asset": form.instance,
            "form": form,
            "current_assignment": None,
            "create_mode": True,
        },
    )


@login_required
def asset_edit_view(request, asset_id):
    ensure_administrator(request.user)
    asset = get_object_or_404(get_all_assets(), pk=asset_id)
    form = AssetAdminForm(instance=asset)

    if request.method == "POST":
        form = AssetAdminForm(request.POST, instance=asset)
        if form.is_valid():
            _, changed_fields = update_asset_details(
                asset=asset,
                actor=request.user,
                data=form.cleaned_data,
            )
            if changed_fields:
                messages.success(request, "Карточка оборудования обновлена.")
            else:
                messages.success(request, "Изменений не обнаружено.")
            return redirect("asset-admin")
        messages.error(request, "Не удалось сохранить изменения. Проверьте форму.")

    return render(
        request,
        "inventory_edit.html",
        {
            "user_data": request.user,
            "asset": asset,
            "form": form,
            "current_assignment": asset.current_assignment,
            "create_mode": False,
        },
    )
