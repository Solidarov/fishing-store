from django.urls import path
from users.views import (
    RegisterView,
    UserLoginView,
    UserLogoutView,
    LogoutConfirmView,
    ProfileView,
    ProfileUpdateView,
    ProfileDeleteView,
)

app_name = "users"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("logout/confirm/", LogoutConfirmView.as_view(), name="logout_confirm"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),
    path("profile/delete/", ProfileDeleteView.as_view(), name="profile_delete"),
]
