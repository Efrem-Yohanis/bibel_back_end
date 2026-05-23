"""
Auth URLs - Authentication endpoints
"""

from django.urls import path
from ..views.auth import (
    RegisterView, LoginView, LogoutView,
    ForgotPasswordView, ResetPasswordView
)

urlpatterns = [
    # Authentication (Public)
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    
    # Password Management (Public)
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
]