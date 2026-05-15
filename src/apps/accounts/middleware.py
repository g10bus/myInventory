from django.contrib.auth import SESSION_KEY, get_user_model, logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class ForceLogoutInactiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._has_inactive_authenticated_user(request):
            logout(request)
            messages.error(request, "Ваш аккаунт заблокирован. Вход в систему недоступен.")
            return redirect(reverse("login"))

        return self.get_response(request)

    def _has_inactive_authenticated_user(self, request):
        if request.user.is_authenticated:
            return not request.user.is_active

        session_user_id = request.session.get(SESSION_KEY)
        if not session_user_id:
            return False

        user_model = get_user_model()
        return user_model.objects.filter(pk=session_user_id, is_active=False).exists()
