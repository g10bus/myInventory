from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.core.access import admin_required
from apps.dashboard.selectors import build_admin_analytics_context, build_dashboard_context


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("home")
    return redirect("login")


@login_required
def home_view(request):
    context = {"user_data": request.user}
    context.update(build_dashboard_context(request.user))
    return render(request, "main.html", context)

@login_required
@admin_required
def analytics_view(request):
    context = {"user_data": request.user}
    context.update(build_admin_analytics_context(request.user))
    return render(request, "analytics.html", context)
