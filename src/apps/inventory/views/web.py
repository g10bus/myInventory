from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.inventory.models import Asset

from ..selectors import get_user_assets


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
