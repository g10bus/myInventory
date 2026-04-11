from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.dashboard.selectors import build_dashboard_context


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("home")
    return redirect("login")


@login_required
def home_view(request):
    context = {"user_data": request.user}
    context.update(build_dashboard_context(request.user))
    return render(request, "main.html", context)
