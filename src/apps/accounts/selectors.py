from django.db.models import Count, Q

from apps.accounts.models import User


def get_manageable_users(query=""):
    users = (
        User.objects.select_related("department")
        .annotate(
            current_assets_count=Count(
                "asset_assignments",
                filter=Q(asset_assignments__is_current=True),
                distinct=True,
            )
        )
        .order_by("last_name", "first_name", "email")
    )
    if query:
        users = users.filter(
            Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(middle_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(role__icontains=query)
            | Q(position__icontains=query)
            | Q(department__name__icontains=query)
        )
    return users
