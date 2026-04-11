from django.contrib.auth.views import LogoutView
from django.urls import path

from .views.web import profile_view, register_view, user_login_view


urlpatterns = [
    path("login/", user_login_view, name="login"),
    path("registration/", register_view, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", profile_view, name="profile"),
]
