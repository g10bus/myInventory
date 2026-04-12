from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.custody.models import AssetAssignment, TransferRequest

from ..forms import LoginForm, ProfileSettingsForm, RegistrationForm, StyledPasswordChangeForm


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
        login(request, user)
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
