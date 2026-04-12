from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.selectors import get_manageable_users
from apps.custody.models import AssetAssignment, TransferRequest

from ..forms import (
    LoginForm,
    ProfileSettingsForm,
    RegistrationForm,
    StyledPasswordChangeForm,
    UserAdminManageForm,
)


def ensure_administrator(user):
    if not user.is_administrator:
        raise PermissionDenied("Доступ разрешён только администраторам.")


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
                messages.success(request, "Профиль обновлен.")
                return redirect("profile")
            messages.error(request, "Не удалось обновить профиль. Проверьте введенные данные.")

        elif action == "change_password":
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Пароль успешно изменен.")
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
def user_admin_view(request):
    ensure_administrator(request.user)
    query = request.GET.get("q", "").strip()
    users = get_manageable_users(query=query)
    return render(
        request,
        "user_admin.html",
        {
            "user_data": request.user,
            "users": users,
            "query": query,
        },
    )


@login_required
def user_edit_view(request, user_id):
    ensure_administrator(request.user)
    managed_user = get_object_or_404(get_manageable_users(), pk=user_id)
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
