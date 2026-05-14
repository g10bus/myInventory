from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.core.pdf import (
    _load_reportlab,
    build_kv_table,
    build_long_table,
    build_pdf_response,
    build_pdf_styles,
    pdf_paragraph,
)

from .models import TransferRequest
from .selectors import get_user_history


def _format_datetime(value):
    if not value:
        return "Не указано"
    localized_value = timezone.localtime(value) if timezone.is_aware(value) else value
    return localized_value.strftime("%d.%m.%Y %H:%M")


def _safe_name(user):
    if not user:
        return "Не указано"
    return user.full_name or user.email


def build_history_report_response(*, user):
    styles = build_pdf_styles()
    reportlab = _load_reportlab()
    Spacer = reportlab["Spacer"]
    mm = reportlab["mm"]

    history_items = list(get_user_history(user))
    story = [
        pdf_paragraph("Отчет по истории операций с ТМЦ", styles["Title"]),
        pdf_paragraph(f"Сформировано для: {_safe_name(user)} ({user.email})", styles["PdfMeta"]),
        pdf_paragraph(f"Дата формирования: {_format_datetime(timezone.now())}", styles["PdfMeta"]),
        Spacer(1, 5 * mm),
    ]

    if history_items:
        story.append(
            build_long_table(
                ["Дата и время", "Событие", "ТМЦ", "Инициатор", "Описание"],
                [
                    [
                        _format_datetime(item.occurred_at),
                        item.get_event_type_display(),
                        (
                            f"{item.asset.title}\nИнв. № {item.asset.inventory_number}"
                            if item.asset
                            else "Системное событие"
                        ),
                        _safe_name(item.actor) if item.actor else "Система",
                        item.message or "Описание не указано",
                    ]
                    for item in history_items
                ],
                styles,
                col_widths=[28 * mm, 34 * mm, 42 * mm, 32 * mm, 54 * mm],
            )
        )
    else:
        story.append(
            pdf_paragraph(
                "Для выбранного пользователя пока нет событий, связанных с движением ТМЦ.",
                styles["BodyText"],
            )
        )

    return build_pdf_response(
        filename=f"history-report-{user.pk}.pdf",
        title="Отчет по истории операций с ТМЦ",
        subject="История операций с ТМЦ",
        story=story,
    )


def get_transfer_for_report(*, actor, transfer_id):
    queryset = TransferRequest.objects.select_related(
        "asset",
        "from_employee",
        "to_employee",
        "processed_by",
    )
    if not actor.is_administrator:
        queryset = queryset.filter(Q(from_employee=actor) | Q(to_employee=actor))
    return get_object_or_404(queryset, pk=transfer_id)


def build_transfer_report_response(*, transfer):
    styles = build_pdf_styles()
    reportlab = _load_reportlab()
    Spacer = reportlab["Spacer"]
    mm = reportlab["mm"]

    asset = transfer.asset
    current_assignment = asset.current_assignment

    story = [
        pdf_paragraph("Отчет по передаче ТМЦ", styles["Title"]),
        pdf_paragraph(f"Заявка № {transfer.pk} от {_format_datetime(transfer.requested_at)}", styles["PdfMeta"]),
        pdf_paragraph(f"Статус на момент формирования: {transfer.get_status_display()}", styles["PdfMeta"]),
        Spacer(1, 5 * mm),
        pdf_paragraph("Сведения о ТМЦ", styles["Heading2"]),
        build_kv_table(
            [
                ("Наименование", asset.title),
                ("Инвентарный номер", asset.inventory_number),
                ("Серийный номер", asset.serial_number or "Не указан"),
                ("Категория", asset.category),
                ("Текущий статус", asset.get_status_display()),
                ("Текущее местоположение", asset.location or "Не указано"),
            ],
            styles,
        ),
        Spacer(1, 5 * mm),
        pdf_paragraph("Участники передачи", styles["Heading2"]),
        build_kv_table(
            [
                ("Отправитель", _safe_name(transfer.from_employee)),
                ("Получатель", _safe_name(transfer.to_employee)),
                (
                    "Обработал заявку",
                    _safe_name(transfer.processed_by) if transfer.processed_by else "Еще не обработано",
                ),
            ],
            styles,
        ),
        Spacer(1, 5 * mm),
        pdf_paragraph("Параметры заявки", styles["Heading2"]),
        build_kv_table(
            [
                ("Дата создания", _format_datetime(transfer.requested_at)),
                ("Дата обработки", _format_datetime(transfer.processed_at) if transfer.processed_at else "Еще не обработано"),
                ("Комментарий", transfer.comment or "Комментарий не указан"),
                (
                    "Текущий ответственный",
                    _safe_name(current_assignment.employee) if current_assignment else "Нет активного закрепления",
                ),
            ],
            styles,
        ),
    ]

    return build_pdf_response(
        filename=f"transfer-report-{transfer.pk}.pdf",
        title=f"Отчет по передаче ТМЦ #{transfer.pk}",
        subject="Передача товарно-материальной ценности",
        story=story,
    )
