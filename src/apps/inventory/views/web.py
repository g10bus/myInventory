from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.core.access import admin_required, post_only
from apps.inventory.forms import (
    AssetAdminForm,
    EmployeeInventoryAssignmentForm,
    InventoryVerificationCreateForm,
)
from apps.inventory.models import Asset
from apps.inventory.services import (
    create_asset,
    create_employee_inventory_assignment,
    record_verification,
    revoke_employee_inventory_assignment,
    update_asset_details,
)
from apps.inventory.ui import (
    annotate_inventory_verification_status,
    build_verification_form_initial,
    build_verification_records,
    resolve_inventory_window,
)

from ..selectors import (
    get_all_assets,
    get_asset_category_choices,
    get_asset_employee_choices,
    get_asset_location_choices,
    get_employee_inventory_assignment_history,
    get_employee_inventory_assignment_choices,
    get_employee_inventory_assignments,
    get_user_assets,
)


@login_required
def my_assets_view(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    category = request.GET.get("category", "").strip()
    inventory_window = resolve_inventory_window(request.user)
    assets = get_user_assets(request.user, query=query, status=status, category=category)
    assets = annotate_inventory_verification_status(
        assets,
        user=request.user,
        active_assignment=inventory_window["active_inventory_assignment"],
    )
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
            **inventory_window,
        },
    )


@login_required
def my_asset_detail_view(request, inventory_number):
    asset = get_object_or_404(
        get_user_assets(request.user),
        inventory_number=inventory_number,
    )
    current_assignment = asset.current_assignment
    inventory_window = resolve_inventory_window(request.user)

    if request.method == "POST":
        if not inventory_window["verification_allowed"]:
            messages.error(request, inventory_window["verification_lock_message"])
            return redirect("mytmc-detail", inventory_number=asset.inventory_number)

        verification_form = InventoryVerificationCreateForm(request.POST, request.FILES)
        if verification_form.is_valid():
            record_verification(
                asset=asset,
                actor=request.user,
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
            **inventory_window,
        },
    )


@login_required
@admin_required
def asset_admin_view(request):
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
@admin_required
def inventory_assignment_admin_view(request):
    employee_query = request.GET.get("employee_q", "").strip()
    employee_choices = get_employee_inventory_assignment_choices()
    form = EmployeeInventoryAssignmentForm(
        request.POST or None,
        employee_queryset=employee_choices,
    )

    if request.method == "POST" and form.is_valid():
        assignment = create_employee_inventory_assignment(
            employee=form.cleaned_data["employee"],
            actor=request.user,
            date_from=form.cleaned_data["date_from"],
            date_to=form.cleaned_data["date_to"],
            note=form.cleaned_data["note"],
        )
        messages.success(
            request,
            (
                f"Инвентаризация назначена сотруднику "
                f"{assignment.employee.full_name} на период "
                f"{assignment.date_from:%d.%m.%Y} - {assignment.date_to:%d.%m.%Y}."
            ),
        )
        return redirect("inventory-assignment-admin")

    return render(
        request,
        "inventory_assignment_admin.html",
        {
            "user_data": request.user,
            "form": form,
            "employee_query": employee_query,
            "assignment_history": get_employee_inventory_assignment_history(employee_query=employee_query),
        },
    )


@login_required
@admin_required
@post_only
def inventory_assignment_revoke_view(request, assignment_id):
    assignment = get_object_or_404(get_employee_inventory_assignments(), pk=assignment_id)
    if assignment.revoked_at:
        messages.info(request, "Назначение уже было отозвано ранее.")
        return redirect("inventory-assignment-admin")

    revoke_employee_inventory_assignment(assignment=assignment, actor=request.user)
    messages.success(
        request,
        (
            f"Назначение инвентаризации для {assignment.employee.full_name} "
            f"за период {assignment.date_from:%d.%m.%Y} - {assignment.date_to:%d.%m.%Y} отозвано."
        ),
    )
    return redirect("inventory-assignment-admin")


@login_required
@admin_required
def asset_create_view(request):
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
@admin_required
def asset_edit_view(request, asset_id):
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
