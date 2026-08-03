from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path("me/avatar/", views.AvatarUploadView.as_view(), name="auth-me-avatar"),
    path("oauth/<str:provider>/token/", views.OAuthLoginView.as_view(), name="auth-oauth-token"),
    path("mfa/enroll/", views.MFAEnrollView.as_view(), name="auth-mfa-enroll"),
    path("mfa/verify/", views.MFAVerifyView.as_view(), name="auth-mfa-verify"),
    path("mfa/login-verify/", views.MFALoginVerifyView.as_view(), name="auth-mfa-login-verify"),
]
