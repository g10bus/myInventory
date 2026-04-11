from django.db import transaction
from django.utils import timezone

from apps.audit.services import log_event
from apps.custody.models import AssetAssignment, TransferRequest
from apps.inventory.models import Asset


class CustodyError(Exception):
    pass


@transaction.atomic
def issue_asset(*, asset, employee, actor, note=""):
    current_assignment = AssetAssignment.objects.select_for_update().filter(
        asset=asset,
        is_current=True,
    )
    if current_assignment.exists():
        raise CustodyError("ТМЦ уже закреплено за другим сотрудником.")

    asset.status = Asset.Status.IN_USE
    asset.location = employee.office_location or asset.location
    asset.save(update_fields=["status", "location", "updated_at"])

    assignment = AssetAssignment.objects.create(
        asset=asset,
        employee=employee,
        assigned_by=actor,
        assigned_at=timezone.now(),
        location_at_issue=asset.location,
        note=note,
    )
    log_event(
        event_type="asset_issued",
        actor=actor,
        related_user=employee,
        asset=asset,
        message=f"ТМЦ '{asset.title}' закреплено за {employee.short_name}.",
        metadata={"assignment_id": assignment.id},
    )
    return assignment


@transaction.atomic
def return_asset(*, asset, actor, note="", location="Склад"):
    current_assignment = AssetAssignment.objects.select_for_update().filter(
        asset=asset,
        is_current=True,
    ).first()
    if not current_assignment:
        raise CustodyError("У ТМЦ нет активного закрепления.")

    current_assignment.is_current = False
    current_assignment.returned_at = timezone.now()
    current_assignment.note = note or current_assignment.note
    current_assignment.save(update_fields=["is_current", "returned_at", "note", "updated_at"])

    asset.status = Asset.Status.RESERVE
    asset.location = location
    asset.save(update_fields=["status", "location", "updated_at"])

    log_event(
        event_type="asset_returned",
        actor=actor,
        related_user=current_assignment.employee,
        asset=asset,
        message=f"ТМЦ '{asset.title}' возвращено из закрепления сотрудника {current_assignment.employee.short_name}.",
        metadata={"assignment_id": current_assignment.id},
    )
    return current_assignment


@transaction.atomic
def request_transfer(*, asset, from_employee, to_employee, actor, comment=""):
    current_assignment = AssetAssignment.objects.select_for_update().filter(
        asset=asset,
        is_current=True,
    ).first()
    if not current_assignment or current_assignment.employee_id != from_employee.id:
        raise CustodyError("Нельзя создать передачу: ТМЦ не закреплено за отправителем.")

    if TransferRequest.objects.filter(asset=asset, status=TransferRequest.Status.PENDING).exists():
        raise CustodyError("Для этого ТМЦ уже есть активная заявка на передачу.")

    transfer = TransferRequest.objects.create(
        asset=asset,
        from_employee=from_employee,
        to_employee=to_employee,
        comment=comment,
    )
    log_event(
        event_type="transfer_requested",
        actor=actor,
        related_user=to_employee,
        asset=asset,
        message=f"Создана заявка на передачу '{asset.title}' от {from_employee.short_name} к {to_employee.short_name}.",
        metadata={"transfer_request_id": transfer.id},
    )
    return transfer


@transaction.atomic
def approve_transfer(*, transfer, actor):
    transfer = TransferRequest.objects.select_for_update().select_related(
        "asset",
        "from_employee",
        "to_employee",
    ).get(pk=transfer.pk)
    if transfer.status != TransferRequest.Status.PENDING:
        raise CustodyError("Заявка уже обработана.")

    current_assignment = AssetAssignment.objects.select_for_update().filter(
        asset=transfer.asset,
        is_current=True,
    ).first()
    if not current_assignment or current_assignment.employee_id != transfer.from_employee_id:
        raise CustodyError("Текущий владелец ТМЦ уже изменился.")

    current_assignment.is_current = False
    current_assignment.returned_at = timezone.now()
    current_assignment.save(update_fields=["is_current", "returned_at", "updated_at"])

    transfer.asset.location = transfer.to_employee.office_location or transfer.asset.location
    transfer.asset.status = Asset.Status.IN_USE
    transfer.asset.save(update_fields=["location", "status", "updated_at"])

    assignment = AssetAssignment.objects.create(
        asset=transfer.asset,
        employee=transfer.to_employee,
        assigned_by=actor,
        assigned_at=timezone.now(),
        location_at_issue=transfer.asset.location,
        note=f"Передача по заявке #{transfer.pk}.",
    )

    transfer.status = TransferRequest.Status.COMPLETED
    transfer.processed_at = timezone.now()
    transfer.processed_by = actor
    transfer.save(update_fields=["status", "processed_at", "processed_by", "updated_at"])

    log_event(
        event_type="transfer_approved",
        actor=actor,
        related_user=transfer.to_employee,
        asset=transfer.asset,
        message=f"Передача '{transfer.asset.title}' подтверждена. Новый ответственный: {transfer.to_employee.short_name}.",
        metadata={"transfer_request_id": transfer.id, "assignment_id": assignment.id},
    )
    return transfer


@transaction.atomic
def reject_transfer(*, transfer, actor):
    transfer = TransferRequest.objects.select_for_update().get(pk=transfer.pk)
    if transfer.status != TransferRequest.Status.PENDING:
        raise CustodyError("Заявка уже обработана.")

    transfer.status = TransferRequest.Status.REJECTED
    transfer.processed_at = timezone.now()
    transfer.processed_by = actor
    transfer.save(update_fields=["status", "processed_at", "processed_by", "updated_at"])

    log_event(
        event_type="transfer_rejected",
        actor=actor,
        related_user=transfer.to_employee,
        asset=transfer.asset,
        message=f"Передача '{transfer.asset.title}' отклонена.",
        metadata={"transfer_request_id": transfer.id},
    )
    return transfer
