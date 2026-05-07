from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.inventory.forms import AssetAdminForm, InventoryVerificationCreateForm
from apps.inventory.models import Asset
from apps.inventory.services import create_asset, record_verification, update_asset_details

from ..selectors import (
    get_all_assets,
    get_asset_category_choices,
    get_asset_employee_choices,
    get_asset_location_choices,
    get_user_assets,
)


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

        location = metadata.get("location") or asset.location
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


def build_verification_form_initial(asset):
    current_assignment = asset.current_assignment
    location = asset.location
    if not location and current_assignment:
        location = current_assignment.location_at_issue

    return {
        "location": location,
        "next_verification_date": asset.next_verification_date,
    }


@login_required
def my_assets_view(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()
    assets = get_user_assets(request.user, query=query, status=status, category=category)
    category_choices = get_asset_category_choices(get_user_assets(request.user))
    return render(
        request,
        "tmc.html",
        {
            "user_data": request.user,
            "assets": assets,
            "query": query,
            "selected_status": status,
            "selected_category": category,
            "status_choices": Asset.Status.choices,
            "category_choices": category_choices,
        },
    )


@login_required
def my_asset_detail_view(request, inventory_number):
    asset = get_object_or_404(
        get_user_assets(request.user),
        inventory_number=inventory_number,
    )
    current_assignment = asset.current_assignment

    if request.method == "POST":
        verification_form = InventoryVerificationCreateForm(request.POST, request.FILES)
        if verification_form.is_valid():
            record_verification(
                asset=asset,
                actor=request.user,
                next_verification_date=verification_form.cleaned_data["next_verification_date"],
                note=verification_form.cleaned_data["note"],
                location=verification_form.cleaned_data["location"],
                image=verification_form.cleaned_data["image"],
                image_caption=verification_form.cleaned_data["image_caption"],
            )
            messages.success(request, "Фиксация сверки сохранена.")
            return redirect("mytmc-detail", inventory_number=asset.inventory_number)
        messages.error(request, "Не удалось сохранить фиксацию. Проверьте заполненные поля.")
    else:
        verification_form = InventoryVerificationCreateForm(initial=build_verification_form_initial(asset))

    verification_is_overdue = bool(
        asset.next_verification_date and asset.next_verification_date < timezone.localdate()
    )
    return render(
        request,
        "tmc_detail.html",
        {
            "user_data": request.user,
            "asset": asset,
            "current_assignment": current_assignment,
            "verification_records": build_verification_records(asset),
            "verification_is_overdue": verification_is_overdue,
            "verification_form": verification_form,
        },
    )


@login_required
def asset_admin_view(request):
    ensure_administrator(request.user)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()
    employee = request.GET.get("employee", "").strip()
    location = request.GET.get("location", "").strip()
    verification_date_from_raw = request.GET.get("verification_date_from", "").strip()
    verification_date_to_raw = request.GET.get("verification_date_to", "").strip()
    verification_date_from = parse_date(verification_date_from_raw) if verification_date_from_raw else None
    verification_date_to = parse_date(verification_date_to_raw) if verification_date_to_raw else None
    assets = get_all_assets(
        query=query,
        status=status,
        category=category,
        employee=employee,
        location=location,
        verification_date_from=verification_date_from,
        verification_date_to=verification_date_to,
    )
    category_choices = get_asset_category_choices(get_all_assets())
    employee_choices = get_asset_employee_choices()
    location_choices = get_asset_location_choices(get_all_assets())
    return render(
        request,
        "inventory_admin.html",
        {
            "user_data": request.user,
            "assets": assets,
            "query": query,
            "selected_status": status,
            "selected_category": category,
            "selected_employee": employee,
            "selected_location": location,
            "selected_verification_date_from": verification_date_from_raw,
            "selected_verification_date_to": verification_date_to_raw,
            "status_choices": Asset.Status.choices,
            "category_choices": category_choices,
            "employee_choices": employee_choices,
            "location_choices": location_choices,
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
