from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.custody.forms import AdminTransferRequestForm, AssetIssueForm, AssetReturnForm, TransferRequestForm
from apps.custody.models import TransferRequest
from apps.custody.selectors import get_custody_admin_context, get_transfer_context, get_user_history
from apps.custody.services import (
    CustodyError,
    approve_transfer,
    issue_asset,
    reject_transfer,
    request_transfer,
    return_asset,
)
from apps.inventory.models import Asset


def ensure_administrator(user):
    if not user.is_administrator:
        raise PermissionDenied("Доступ разрешен только администраторам.")


@login_required
def history_view(request):
    return render(
        request,
        "history.html",
        {
            "user_data": request.user,
            "activity_feed": get_user_history(request.user),
        },
    )


@login_required
def transfers_view(request):
    context = get_transfer_context(request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create_transfer":
            asset = get_object_or_404(
                Asset.objects.filter(assignments__employee=request.user, assignments__is_current=True),
                pk=request.POST.get("asset_id"),
            )
            recipient = get_object_or_404(context["colleagues"], pk=request.POST.get("recipient_id"))
            try:
                request_transfer(
                    asset=asset,
                    from_employee=request.user,
                    to_employee=recipient,
                    actor=request.user,
                    comment=request.POST.get("comment", "").strip(),
                )
                messages.success(request, "Заявка на передачу создана.")
            except CustodyError as exc:
                messages.error(request, str(exc))
            return redirect("exchange")

        if action == "process_transfer":
            transfer = get_object_or_404(
                TransferRequest.objects.filter(to_employee=request.user),
                pk=request.POST.get("transfer_id"),
            )
            decision = request.POST.get("decision")
            try:
                if decision == "approve":
                    approve_transfer(transfer=transfer, actor=request.user)
                    messages.success(request, "Передача успешно завершена.")
                elif decision == "reject":
                    reject_transfer(transfer=transfer, actor=request.user)
                    messages.success(request, "Заявка отклонена.")
            except CustodyError as exc:
                messages.error(request, str(exc))
            return redirect("exchange")

    context["user_data"] = request.user
    context["form"] = TransferRequestForm(
        asset_queryset=context["current_assets"],
        recipient_queryset=context["colleagues"],
    )
    return render(request, "exchange.html", context)


@login_required
def custody_admin_view(request):
    ensure_administrator(request.user)
    context = get_custody_admin_context()

    issue_form = AssetIssueForm(
        asset_queryset=context["issue_asset_queryset"],
        employee_queryset=context["employees"],
    )
    return_form = AssetReturnForm(
        assignment_queryset=context["assignment_queryset"],
    )
    transfer_form = AdminTransferRequestForm(
        asset_queryset=context["transfer_asset_queryset"],
        recipient_queryset=context["employees"],
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "issue_asset":
            issue_form = AssetIssueForm(
                request.POST,
                asset_queryset=context["issue_asset_queryset"],
                employee_queryset=context["employees"],
            )
            if issue_form.is_valid():
                try:
                    assignment = issue_asset(
                        asset=issue_form.cleaned_data["asset"],
                        employee=issue_form.cleaned_data["employee"],
                        actor=request.user,
                        note=issue_form.cleaned_data["note"].strip(),
                    )
                    messages.success(
                        request,
                        f"ТМЦ '{assignment.asset.title}' выдано сотруднику {assignment.employee.short_name}.",
                    )
                    return redirect("custody-admin")
                except CustodyError as exc:
                    messages.error(request, str(exc))

        elif action == "return_asset":
            return_form = AssetReturnForm(
                request.POST,
                assignment_queryset=context["assignment_queryset"],
            )
            if return_form.is_valid():
                assignment = return_form.cleaned_data["assignment"]
                try:
                    return_asset(
                        asset=assignment.asset,
                        actor=request.user,
                        note=return_form.cleaned_data["note"].strip(),
                        location=return_form.cleaned_data["location"].strip() or "Склад",
                    )
                    messages.success(
                        request,
                        f"ТМЦ '{assignment.asset.title}' возвращено и переведено в резерв.",
                    )
                    return redirect("custody-admin")
                except CustodyError as exc:
                    messages.error(request, str(exc))

        elif action == "create_admin_transfer":
            transfer_form = AdminTransferRequestForm(
                request.POST,
                asset_queryset=context["transfer_asset_queryset"],
                recipient_queryset=context["employees"],
            )
            if transfer_form.is_valid():
                current_assignment = transfer_form.cleaned_data["current_assignment"]
                try:
                    transfer = request_transfer(
                        asset=transfer_form.cleaned_data["asset"],
                        from_employee=current_assignment.employee,
                        to_employee=transfer_form.cleaned_data["recipient"],
                        actor=request.user,
                        comment=transfer_form.cleaned_data["comment"].strip(),
                    )
                    messages.success(
                        request,
                        (
                            f"Заявка на передачу '{transfer.asset.title}' оформлена "
                            f"от {transfer.from_employee.short_name} к {transfer.to_employee.short_name}."
                        ),
                    )
                    return redirect("custody-admin")
                except CustodyError as exc:
                    messages.error(request, str(exc))

        elif action == "process_transfer":
            transfer = get_object_or_404(TransferRequest.objects.all(), pk=request.POST.get("transfer_id"))
            decision = request.POST.get("decision")
            try:
                if decision == "approve":
                    approve_transfer(transfer=transfer, actor=request.user)
                    messages.success(request, "Передача подтверждена и исполнена.")
                elif decision == "reject":
                    reject_transfer(transfer=transfer, actor=request.user)
                    messages.success(request, "Передача отклонена.")
                else:
                    messages.error(request, "Неизвестное действие для обработки передачи.")
                return redirect("custody-admin")
            except CustodyError as exc:
                messages.error(request, str(exc))

    return render(
        request,
        "custody_admin.html",
        {
            "user_data": request.user,
            "issue_form": issue_form,
            "return_form": return_form,
            "transfer_form": transfer_form,
            "current_assignments": context["assignment_queryset"],
            "pending_transfers": context["pending_transfers"],
            "recent_transfers": context["recent_transfers"],
        },
    )
