from collections import defaultdict

from django.db.models import Prefetch, Q
from django.utils import timezone

from apps.accounts.models import User
from apps.custody.models import AssetAssignment
from apps.inventory.models import Asset, EmployeeInventoryAssignment, InventoryVerification


def get_asset_category_choices(queryset):
    return list(
        queryset.exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )


def get_asset_location_choices(queryset):
    return list(
        queryset.exclude(location="")
        .values_list("location", flat=True)
        .distinct()
        .order_by("location")
    )


def get_asset_employee_choices():
    return (
        User.objects.filter(asset_assignments__is_current=True)
        .distinct()
        .order_by("last_name", "first_name", "email")
    )


def get_employee_inventory_assignment_choices():
    return (
        User.objects.filter(is_active=True, asset_assignments__is_current=True)
        .select_related("department")
        .distinct()
        .order_by("last_name", "first_name", "email")
    )


def get_user_assets(user, query="", status="", category=""):
    assets = (
        Asset.objects.filter(assignments__employee=user, assignments__is_current=True)
        .distinct()
        .order_by("category", "title", "inventory_number")
    )
    if query:
        assets = assets.filter(
            Q(title__icontains=query)
            | Q(model_name__icontains=query)
            | Q(category__icontains=query)
            | Q(inventory_number__icontains=query)
            | Q(serial_number__icontains=query)
        )
    if status:
        assets = assets.filter(status=status)
    if category:
        assets = assets.filter(category=category)
    return assets


def get_all_assets(
    query="",
    status="",
    category="",
    employee="",
    location="",
    verification_date_from=None,
    verification_date_to=None,
):
    assets = (
        Asset.objects.prefetch_related(
            Prefetch(
                "assignments",
                queryset=AssetAssignment.objects.filter(is_current=True).select_related("employee"),
                to_attr="current_assignments",
            )
        )
        .order_by("category", "title", "inventory_number")
    )
    if query:
        assets = assets.filter(
            Q(title__icontains=query)
            | Q(model_name__icontains=query)
            | Q(category__icontains=query)
            | Q(inventory_number__icontains=query)
            | Q(serial_number__icontains=query)
            | Q(location__icontains=query)
        )
    if status:
        assets = assets.filter(status=status)
    if category:
        assets = assets.filter(category=category)
    if employee:
        assets = assets.filter(assignments__is_current=True, assignments__employee_id=employee)
    if location:
        assets = assets.filter(location=location)
    if verification_date_from:
        assets = assets.filter(next_verification_date__gte=verification_date_from)
    if verification_date_to:
        assets = assets.filter(next_verification_date__lte=verification_date_to)
    return assets


def get_employee_inventory_assignments(*, employee_query=""):
    assignments = (
        EmployeeInventoryAssignment.objects.select_related("employee", "employee__department", "assigned_by")
        .order_by("-date_from", "-created_at")
    )
    if employee_query:
        assignments = assignments.filter(
            Q(employee__email__icontains=employee_query)
            | Q(employee__first_name__icontains=employee_query)
            | Q(employee__last_name__icontains=employee_query)
            | Q(employee__middle_name__icontains=employee_query)
            | Q(employee__department__name__icontains=employee_query)
        )
    return assignments


def get_employee_inventory_assignment_history(*, employee_query=""):
    assignments = list(get_employee_inventory_assignments(employee_query=employee_query))
    if not assignments:
        return assignments

    employee_ids = {assignment.employee_id for assignment in assignments}
    asset_ids_by_employee = defaultdict(set)
    for employee_id, asset_id in AssetAssignment.objects.filter(
        employee_id__in=employee_ids,
        is_current=True,
    ).values_list("employee_id", "asset_id"):
        asset_ids_by_employee[employee_id].add(asset_id)

    verifications_by_employee = defaultdict(list)
    for employee_id, asset_id, verified_date in InventoryVerification.objects.filter(
        responsible_employee_id__in=employee_ids,
    ).values_list("responsible_employee_id", "asset_id", "verified_at__date"):
        verifications_by_employee[employee_id].append((asset_id, verified_date))

    for assignment in assignments:
        assigned_asset_ids = asset_ids_by_employee.get(assignment.employee_id, set())
        verified_asset_ids = {
            asset_id
            for asset_id, verified_date in verifications_by_employee.get(assignment.employee_id, [])
            if assignment.date_from <= verified_date <= assignment.date_to and asset_id in assigned_asset_ids
        }
        assignment.assigned_assets_total = len(assigned_asset_ids)
        assignment.verified_assets_total = len(verified_asset_ids)
        assignment.has_completed_photo_fixations = (
            not assignment.is_revoked
            and assignment.assigned_assets_total > 0
            and assignment.verified_assets_total >= assignment.assigned_assets_total
        )

    return assignments


def get_user_inventory_assignments(user):
    return (
        EmployeeInventoryAssignment.objects.filter(employee=user, revoked_at__isnull=True)
        .select_related("assigned_by")
        .order_by("date_from", "date_to", "-created_at")
    )


def get_active_inventory_assignment(user, on_date=None):
    target_date = on_date or timezone.localdate()
    return (
        EmployeeInventoryAssignment.objects.filter(
            employee=user,
            revoked_at__isnull=True,
            date_from__lte=target_date,
            date_to__gte=target_date,
        )
        .order_by("date_from", "-created_at")
        .first()
    )
