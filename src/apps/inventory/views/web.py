from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.inventory.forms import AssetAdminForm
from apps.inventory.models import Asset
from apps.inventory.services import update_asset_details

from ..selectors import get_all_assets, get_user_assets


def ensure_administrator(user):
    if not user.is_administrator:
        raise PermissionDenied("Доступ разрешен только администраторам.")


@login_required
def my_assets_view(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    assets = get_user_assets(request.user, query=query, status=status)
    return render(
        request,
        "tmc.html",
        {
            "user_data": request.user,
            "assets": assets,
            "query": query,
            "selected_status": status,
            "status_choices": Asset.Status.choices,
        },
    )


@login_required
def asset_admin_view(request):
    ensure_administrator(request.user)
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    assets = get_all_assets(query=query, status=status)
    return render(
        request,
        "inventory_admin.html",
        {
            "user_data": request.user,
            "assets": assets,
            "query": query,
            "selected_status": status,
            "status_choices": Asset.Status.choices,
        },
    )


@login_required
def asset_edit_view(request, asset_id):
    ensure_administrator(request.user)
    asset = get_object_or_404(get_all_assets(), pk=asset_id)
    form = AssetAdminForm(instance=asset)

    if request.method == "POST":
        form = AssetAdminForm(request.POST, instance=asset)
        if form.is_valid():
            _, changed_fields = update_asset_details(
                asset=asset,
                actor=request.user,
                data=form.cleaned_data,
            )
            if changed_fields:
                messages.success(request, "Карточка оборудования обновлена.")
            else:
                messages.success(request, "Изменений не обнаружено.")
            return redirect("asset-admin")
        messages.error(request, "Не удалось сохранить изменения. Проверьте форму.")

    return render(
        request,
        "inventory_edit.html",
        {
            "user_data": request.user,
            "asset": asset,
            "form": form,
            "current_assignment": asset.current_assignment,
        },
    )
