from django.contrib.auth.views import LogoutView
from django.urls import path

from .views.web import profile_view, register_view, user_admin_view, user_edit_view, user_login_view


urlpatterns = [
    path("login/", user_login_view, name="login"),
    path("registration/", register_view, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", profile_view, name="profile"),
    path("users/manage/", user_admin_view, name="user-admin"),
    path("users/manage/<int:user_id>/", user_edit_view, name="user-edit"),
]
