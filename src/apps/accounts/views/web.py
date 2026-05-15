from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from apps.accounts.selectors import get_manageable_users
from apps.core.access import admin_required, ensure_administrator, post_only
from apps.custody.models import AssetAssignment, TransferRequest
from apps.org.models import Department

from ..forms import (
    AdminModeConfirmationForm,
    LoginForm,
    ProfileSettingsForm,
    RegistrationForm,
    StyledPasswordChangeForm,
    UserAdminManageForm,
)
from ..ui import ADMIN_UI_MODE, set_user_interface_mode


def resolve_safe_next_url(request, next_url):
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("home")


def parse_int_filter(value):
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def user_login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("home")

    return render(request, "login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="apps.accounts.backends.EmailBackend")
        messages.success(request, "Регистрация завершена. Профиль создан.")
        return redirect("home")
    return render(request, "register.html", {"form": form})


@login_required
def profile_view(request):
    profile_form = ProfileSettingsForm(instance=request.user)
    password_form = StyledPasswordChangeForm(user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            profile_form = ProfileSettingsForm(request.POST, request.FILES, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Профиль обновлён.")
                return redirect("profile")
            messages.error(request, "Не удалось обновить профиль. Проверьте введённые данные.")

        elif action == "change_password":
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Пароль успешно изменён.")
                return redirect("profile")
            messages.error(request, "Не удалось изменить пароль. Проверьте форму.")

    current_assignments = (
        AssetAssignment.objects.filter(employee=request.user, is_current=True)
        .select_related("asset")
        .order_by("asset__category", "asset__title")
    )
    transfer_count = TransferRequest.objects.filter(
        from_employee=request.user,
    ).count() + TransferRequest.objects.filter(to_employee=request.user).count()

    return render(
        request,
        "profile.html",
        {
            "user_data": request.user,
            "profile_form": profile_form,
            "password_form": password_form,
            "current_assignments": current_assignments,
            "transfer_count": transfer_count,
        },
    )


@login_required
@post_only(message="Смена режима интерфейса доступна только через POST-запрос.")
def switch_ui_mode_view(request):
    requested_mode = request.POST.get("mode")
    next_url = resolve_safe_next_url(request, request.POST.get("next", ""))

    if requested_mode == ADMIN_UI_MODE:
        ensure_administrator(request.user)
        confirm_url = reverse("confirm-admin-ui-mode")
        return redirect(f"{confirm_url}?{urlencode({'next': next_url})}")

    set_user_interface_mode(request, requested_mode)
    messages.success(request, "Включён обычный режим.")
    return redirect(next_url)


@login_required
@admin_required(message="Доступ разрешён только администраторам.")
def confirm_admin_ui_mode_view(request):
    next_url = resolve_safe_next_url(request, request.POST.get("next") or request.GET.get("next", ""))
    form = AdminModeConfirmationForm(user=request.user)

    if request.method == "POST":
        form = AdminModeConfirmationForm(request.POST, user=request.user)
        if form.is_valid():
            set_user_interface_mode(request, ADMIN_UI_MODE)
            messages.success(request, "Включён режим администратора.")
            return redirect(next_url)

        messages.error(request, "Не удалось подтвердить пароль.")

    return render(
        request,
        "confirm_admin_mode.html",
        {
            "user_data": request.user,
            "form": form,
            "next_url": next_url,
        },
    )


@login_required
@admin_required(message="Доступ разрешён только администраторам.")
def user_admin_view(request):
    query = request.GET.get("q", "").strip()
    department = request.GET.get("department", "").strip()
    activity = request.GET.get("activity", "").strip()
    admin_access = request.GET.get("admin_access", "").strip()
    assets_count_from = parse_int_filter(request.GET.get("assets_count_from", "").strip())
    assets_count_to = parse_int_filter(request.GET.get("assets_count_to", "").strip())
    users = get_manageable_users(
        query=query,
        actor=request.user,
        department=department,
        activity=activity,
        admin_access=admin_access,
        assets_count_from=assets_count_from,
        assets_count_to=assets_count_to,
    )
    return render(
        request,
        "user_admin.html",
        {
            "user_data": request.user,
            "users": users,
            "query": query,
            "departments": Department.objects.all(),
            "selected_department": department,
            "selected_activity": activity,
            "selected_admin_access": admin_access,
            "selected_assets_count_from": request.GET.get("assets_count_from", "").strip(),
            "selected_assets_count_to": request.GET.get("assets_count_to", "").strip(),
        },
    )


@login_required
@admin_required(message="Доступ разрешён только администраторам.")
def user_edit_view(request, user_id):
    managed_user = get_object_or_404(get_manageable_users(actor=request.user), pk=user_id)
    current_assignments = (
        AssetAssignment.objects.filter(employee=managed_user, is_current=True)
        .select_related("asset")
        .order_by("asset__category", "asset__title")
    )
    form = UserAdminManageForm(instance=managed_user, actor=request.user)

    if request.method == "POST":
        form = UserAdminManageForm(
            request.POST,
            request.FILES,
            instance=managed_user,
            actor=request.user,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Данные пользователя обновлены.")
            return redirect("user-admin")
        messages.error(request, "Не удалось сохранить изменения пользователя.")

    return render(
        request,
        "user_edit.html",
        {
            "user_data": request.user,
            "managed_user": managed_user,
            "form": form,
            "current_assignments": current_assignments,
        },
    )
