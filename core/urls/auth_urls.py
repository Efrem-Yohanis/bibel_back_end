# core/urls/auth_urls.py
from django.urls import path
from ..views.auth import (
    RegisterView, LoginView, LogoutView,
    ForgotPasswordView, ResetPasswordView,
    GoogleLoginView, GoogleAuthRedirectView, GoogleAuthCallbackView
)

urlpatterns = [
    # Traditional Authentication
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    
    # Password Management
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
    
    # Google OAuth2
    path('google/', GoogleLoginView.as_view(), name='google-login'),
    path('google/redirect/', GoogleAuthRedirectView.as_view(), name='google-redirect'),
    path('google/callback/', GoogleAuthCallbackView.as_view(), name='google-callback'),
]