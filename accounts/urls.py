from django.urls import path
from .views import UserLoginView, UserLogoutView, UserRegisterView, UserPasswordResetView

app_name = "accounts"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("password-reset/", UserPasswordResetView.as_view(), name="password_reset"),
]
