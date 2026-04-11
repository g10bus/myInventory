from django.db.models import Q

from apps.audit.models import AuditEvent
from apps.custody.models import TransferRequest
from apps.inventory.selectors import get_user_assets


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
