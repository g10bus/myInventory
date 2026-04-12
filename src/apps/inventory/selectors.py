from django.db.models import Prefetch, Q

from apps.custody.models import AssetAssignment
from apps.inventory.models import Asset


def get_user_assets(user, query="", status=""):
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
    return assets


def get_all_assets(query="", status=""):
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
    return assets
