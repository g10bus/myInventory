from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.audit.models import AuditEvent
from apps.custody.models import AssetAssignment, TransferRequest
from apps.inventory.models import Asset
from apps.inventory.selectors import get_user_assets

User = get_user_model()


def get_transfer_context(user):
    return {
        "current_assets": get_user_assets(user),
        "incoming_requests": (
            TransferRequest.objects.filter(to_employee=user)
            .select_related("asset", "from_employee", "to_employee")
            .order_by("-requested_at")
        ),
        "outgoing_requests": (
            TransferRequest.objects.filter(from_employee=user)
            .select_related("asset", "from_employee", "to_employee")
            .order_by("-requested_at")
        ),
        "colleagues": user.__class__.objects.filter(is_active=True).exclude(pk=user.pk).select_related(
            "department"
        ).order_by("last_name", "first_name", "email"),
    }


def get_user_history(user):
    return AuditEvent.objects.filter(Q(actor=user) | Q(related_user=user)).select_related(
        "actor",
        "related_user",
        "asset",
    ).order_by("-occurred_at")


def get_custody_admin_context():
    employee_queryset = (
        User.objects.filter(is_active=True)
        .select_related("department")
        .order_by("last_name", "first_name", "email")
    )
    issue_asset_queryset = (
        Asset.objects.exclude(assignments__is_current=True)
        .order_by("category", "title", "inventory_number")
        .distinct()
    )
    transfer_asset_queryset = (
        Asset.objects.filter(assignments__is_current=True)
        .order_by("category", "title", "inventory_number")
        .distinct()
    )
    assignment_queryset = (
        AssetAssignment.objects.filter(is_current=True)
        .select_related("asset", "employee", "assigned_by", "employee__department")
        .order_by("asset__category", "asset__title", "asset__inventory_number")
    )
    transfer_queryset = (
        TransferRequest.objects.select_related(
            "asset",
            "from_employee",
            "to_employee",
            "processed_by",
        ).order_by("-requested_at")
    )
    return {
        "employees": employee_queryset,
        "issue_asset_queryset": issue_asset_queryset,
        "transfer_asset_queryset": transfer_asset_queryset,
        "assignment_queryset": assignment_queryset,
        "pending_transfers": transfer_queryset.filter(status=TransferRequest.Status.PENDING),
        "recent_transfers": transfer_queryset[:10],
    }
