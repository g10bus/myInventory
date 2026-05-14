from django.db.models import Count, Q

from apps.accounts.models import User


def get_manageable_users(
    query="",
    actor=None,
    department="",
    activity="",
    admin_access="",
    assets_count_from=None,
    assets_count_to=None,
):
    admin_query = Q(is_superuser=True) | Q(is_staff=True) | Q(groups__name__in=["system_admin", "inventory_operator"])
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
    if actor and actor.pk:
        users = users.exclude(pk=actor.pk)
    if query:
        users = users.filter(
            Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(middle_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(role__icontains=query)
            | Q(position__icontains=query)
            | Q(office_location__icontains=query)
            | Q(department__name__icontains=query)
        )
    if department:
        users = users.filter(department_id=department)
    if activity == "active":
        users = users.filter(is_active=True)
    elif activity == "inactive":
        users = users.filter(is_active=False)
    if admin_access == "admin":
        users = users.filter(admin_query)
    elif admin_access == "regular":
        users = users.exclude(admin_query)
    if assets_count_from is not None:
        users = users.filter(current_assets_count__gte=assets_count_from)
    if assets_count_to is not None:
        users = users.filter(current_assets_count__lte=assets_count_to)
    return users.distinct()
