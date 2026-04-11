from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.custody.forms import TransferRequestForm
from apps.custody.models import TransferRequest
from apps.custody.selectors import get_transfer_context, get_user_history
from apps.custody.services import CustodyError, approve_transfer, reject_transfer, request_transfer
from apps.inventory.models import Asset


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
