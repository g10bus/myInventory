from django.db.models import Q
from django.utils import timezone

from apps.custody.models import AssetAssignment, TransferRequest
from apps.inventory.models import Asset
from apps.inventory.selectors import get_user_assets


def build_dashboard_context(user):
    today = timezone.localdate()
    current_assets = get_user_assets(user)
    pending_incoming = TransferRequest.objects.filter(
        to_employee=user,
        status=TransferRequest.Status.PENDING,
    )
    pending_outgoing = TransferRequest.objects.filter(
        from_employee=user,
        status=TransferRequest.Status.PENDING,
    )

    return {
        "stats_cards": [
            {
                "value": current_assets.count(),
                "label": "Закреплено за мной",
                "hint": "Все активные ТМЦ, оформленные на сотрудника.",
            },
            {
                "value": current_assets.filter(
                    next_verification_date__isnull=False,
                    next_verification_date__lt=today,
                ).count(),
                "label": "Просрочена сверка",
                "hint": "Позиции, которые нужно подтвердить в первую очередь.",
            },
            {
                "value": current_assets.filter(status=Asset.Status.REPAIR).count(),
                "label": "Сейчас в ремонте",
                "hint": "Техника, временно недоступная сотруднику.",
            },
            {
                "value": pending_incoming.count() + pending_outgoing.count(),
                "label": "Передачи в работе",
                "hint": "Заявки на выдачу и прием имущества.",
            },
        ],
        "overall_summary": [
            {"label": "Всего ТМЦ", "value": Asset.objects.count()},
            {
                "label": "Выдано сотрудникам",
                "value": AssetAssignment.objects.filter(is_current=True).count(),
            },
            {
                "label": "В резерве",
                "value": Asset.objects.filter(status=Asset.Status.RESERVE).count(),
            },
            {
                "label": "Сотрудников в системе",
                "value": user.__class__.objects.filter(is_active=True).count(),
            },
        ],
        "upcoming_verifications": current_assets.filter(
            next_verification_date__isnull=False,
        ).order_by("next_verification_date", "title")[:5],
        "recent_transfers": (
            TransferRequest.objects.filter(Q(from_employee=user) | Q(to_employee=user))
            .select_related("asset", "from_employee", "to_employee")
            .order_by("-requested_at")[:5]
        ),
        "user_assets": current_assets[:4],
    }
