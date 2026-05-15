from django.contrib.auth.backends import ModelBackend

from apps.integrations.services.active_directory import authenticate_with_active_directory


class ActiveDirectoryBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = kwargs.get("email") or username
        try:
            user = authenticate_with_active_directory(identifier, password)
        except Exception:
            return None
        if user and self.user_can_authenticate(user):
            return user
        return None

