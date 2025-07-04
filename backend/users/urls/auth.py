from django.urls import path
from users.views import (
    RegisterView, login_view, logout_view, CustomTokenRefreshView, verify_email
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("verify-email/", verify_email, name="verify_email"),
]
