from datetime import date

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.custody.models import AssetAssignment, TransferRequest
from apps.inventory.models import Asset, InventoryVerification
from apps.inventory.selectors import get_user_assets, get_user_inventory_assignments


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
    inventory_assignments = get_user_inventory_assignments(user)
    active_inventory_assignments = inventory_assignments.filter(date_from__lte=today, date_to__gte=today)
    upcoming_inventory_assignments = inventory_assignments.filter(date_from__gt=today)

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
        "active_inventory_assignments": active_inventory_assignments,
        "upcoming_inventory_assignments": upcoming_inventory_assignments[:5],
        "inventory_assignment_count": active_inventory_assignments.count() + upcoming_inventory_assignments.count(),
    }


def _calculate_percent(count, total):
    if not total:
        return 0
    return round((count / total) * 100, 1)


def _build_donut_style(items):
    total = sum(item["count"] for item in items)
    if not total:
        return "conic-gradient(#dfeaf7 0 100%)"

    cursor = 0
    segments = []
    for item in items:
        if item["count"] <= 0:
            continue
        next_cursor = cursor + (item["count"] / total) * 100
        segments.append(f"{item['color']} {cursor:.2f}% {next_cursor:.2f}%")
        cursor = next_cursor

    if not segments:
        return "conic-gradient(#dfeaf7 0 100%)"
    return f"conic-gradient({', '.join(segments)})"


def _month_start_for_offset(today, offset):
    year = today.year
    month = today.month - offset
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def _month_label(month_start):
    return f"{month_start.month:02d}.{month_start.year}"


def _build_month_count_map(queryset, field_name, months):
    month_set = set(months)
    aggregated = (
        queryset.annotate(period=TruncMonth(field_name))
        .values("period")
        .annotate(total=Count("id"))
    )
    counts = {month: 0 for month in months}
    for row in aggregated:
        period = row["period"]
        if hasattr(period, "date"):
            period = period.date()
        period = period.replace(day=1)
        if period in month_set:
            counts[period] = row["total"]
    return counts


def _build_line_points(values, width=320, height=160, padding=18):
    if not values:
        return {"points": "", "dots": [], "max_value": 0}

    max_value = max(values) if max(values) > 0 else 1
    usable_width = max(width - padding * 2, 1)
    usable_height = max(height - padding * 2, 1)
    step = usable_width / max(len(values) - 1, 1)
    dots = []
    for index, value in enumerate(values):
        x = padding + step * index
        y = height - padding - ((value / max_value) * usable_height)
        dots.append({"x": round(x, 2), "y": round(y, 2), "value": value})
    points = " ".join(f"{dot['x']},{dot['y']}" for dot in dots)
    return {"points": points, "dots": dots, "max_value": max(values)}


def build_admin_analytics_context(user):
    today = timezone.localdate()
    total_assets = Asset.objects.count()
    current_assignments = AssetAssignment.objects.filter(is_current=True)
    current_assignments_total = current_assignments.count()
    pending_transfers = TransferRequest.objects.filter(status=TransferRequest.Status.PENDING).count()
    overdue_assets = Asset.objects.filter(
        next_verification_date__isnull=False,
        next_verification_date__lt=today,
    ).count()
    current_month_start = today.replace(day=1)
    verifications_this_month = InventoryVerification.objects.filter(
        verified_at__date__gte=current_month_start,
    ).count()

    asset_status_palette = {
        Asset.Status.IN_USE: "#2f80ed",
        Asset.Status.REPAIR: "#5ab0ff",
        Asset.Status.BROKEN: "#be4d35",
        Asset.Status.RESERVE: "#67b26f",
    }
    asset_status_counts = {
        row["status"]: row["total"]
        for row in Asset.objects.values("status").annotate(total=Count("id"))
    }
    asset_status_chart_items = []
    for status_value, status_label in Asset.Status.choices:
        count = asset_status_counts.get(status_value, 0)
        asset_status_chart_items.append(
            {
                "label": status_label,
                "count": count,
                "share": _calculate_percent(count, total_assets),
                "color": asset_status_palette.get(status_value, "#9fb7d1"),
            }
        )

    transfer_total = TransferRequest.objects.count()
    transfer_status_palette = {
        TransferRequest.Status.PENDING: "#f2994a",
        TransferRequest.Status.COMPLETED: "#2f80ed",
        TransferRequest.Status.REJECTED: "#be4d35",
    }
    transfer_status_counts = {
        row["status"]: row["total"]
        for row in TransferRequest.objects.values("status").annotate(total=Count("id"))
    }
    transfer_status_chart_items = []
    for status_value, status_label in TransferRequest.Status.choices:
        count = transfer_status_counts.get(status_value, 0)
        transfer_status_chart_items.append(
            {
                "label": status_label,
                "count": count,
                "share": _calculate_percent(count, transfer_total),
                "color": transfer_status_palette.get(status_value, "#9fb7d1"),
            }
        )

    category_rows = list(
        Asset.objects.values("category").annotate(total=Count("id")).order_by("-total", "category")[:6]
    )
    category_max = max((row["total"] for row in category_rows), default=1)
    for row in category_rows:
        row["width"] = round((row["total"] / category_max) * 100, 1) if category_max else 0
        row["share"] = _calculate_percent(row["total"], total_assets)

    department_rows = list(
        current_assignments.values("employee__department__name")
        .annotate(total=Count("id"))
        .order_by("-total", "employee__department__name")[:6]
    )
    department_max = max((row["total"] for row in department_rows), default=1)
    for row in department_rows:
        row["label"] = row["employee__department__name"] or "Без отдела"
        row["width"] = round((row["total"] / department_max) * 100, 1) if department_max else 0
        row["share"] = _calculate_percent(row["total"], current_assignments_total)

    months = [_month_start_for_offset(today, offset) for offset in range(5, -1, -1)]
    requested_map = _build_month_count_map(TransferRequest.objects.all(), "requested_at", months)
    completed_map = _build_month_count_map(
        TransferRequest.objects.exclude(processed_at__isnull=True),
        "processed_at",
        months,
    )
    transfer_month_max = max([*requested_map.values(), *completed_map.values()], default=0) or 1
    transfer_activity = []
    for month in months:
        requested_total = requested_map[month]
        completed_total = completed_map[month]
        transfer_activity.append(
            {
                "label": _month_label(month),
                "requested_total": requested_total,
                "completed_total": completed_total,
                "requested_height": round((requested_total / transfer_month_max) * 100, 1) if requested_total else 0,
                "completed_height": round((completed_total / transfer_month_max) * 100, 1) if completed_total else 0,
            }
        )

    verification_map = _build_month_count_map(InventoryVerification.objects.all(), "verified_at", months)
    verification_values = [verification_map[month] for month in months]
    verification_line = _build_line_points(verification_values)
    verification_trend = []
    for month, dot in zip(months, verification_line["dots"]):
        verification_trend.append(
            {
                "label": _month_label(month),
                "value": dot["value"],
                "x": dot["x"],
                "y": dot["y"],
            }
        )

    return {
        "analytics_kpis": [
            {
                "label": "Всего ТМЦ",
                "value": total_assets,
                "hint": "Полный объем имущества в системе.",
            },
            {
                "label": "Активные закрепления",
                "value": current_assignments_total,
                "hint": "ТМЦ, выданные сотрудникам на текущий момент.",
            },
            {
                "label": "Просроченные сверки",
                "value": overdue_assets,
                "hint": "Позиции, требующие внимания администратора.",
            },
            {
                "label": "Заявки в работе",
                "value": pending_transfers,
                "hint": "Неподтвержденные передачи между сотрудниками.",
            },
            {
                "label": "Сверки за месяц",
                "value": verifications_this_month,
                "hint": "Количество подтвержденных инвентаризаций в текущем месяце.",
            },
        ],
        "asset_status_chart": {
            "title": "Распределение ТМЦ по статусам",
            "total": total_assets,
            "style": _build_donut_style(asset_status_chart_items),
            "items": asset_status_chart_items,
        },
        "transfer_status_chart": {
            "title": "Статусы заявок на передачу",
            "total": transfer_total,
            "style": _build_donut_style(transfer_status_chart_items),
            "items": transfer_status_chart_items,
        },
        "category_rows": category_rows,
        "department_rows": department_rows,
        "transfer_activity": transfer_activity,
        "verification_trend": verification_trend,
        "verification_trend_points": verification_line["points"],
        "verification_trend_max": verification_line["max_value"],
    }
