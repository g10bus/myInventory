from django.contrib.auth.views import LogoutView
from django.urls import path

from .views.web import (
    confirm_admin_ui_mode_view,
    profile_view,
    register_view,
    switch_ui_mode_view,
    user_admin_view,
    user_edit_view,
    user_login_view,
)


urlpatterns = [
    path("login/", user_login_view, name="login"),
    path("registration/", register_view, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", profile_view, name="profile"),
    path("profile/switch-mode/confirm/", confirm_admin_ui_mode_view, name="confirm-admin-ui-mode"),
    path("profile/switch-mode/", switch_ui_mode_view, name="switch-ui-mode"),
    path("users/manage/", user_admin_view, name="user-admin"),
    path("users/manage/<int:user_id>/", user_edit_view, name="user-edit"),
]
