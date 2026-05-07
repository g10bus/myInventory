from django.db.models import Prefetch, Q

from apps.accounts.models import User
from apps.custody.models import AssetAssignment
from apps.inventory.models import Asset


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
