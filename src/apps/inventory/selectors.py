from django.db.models import Q

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
