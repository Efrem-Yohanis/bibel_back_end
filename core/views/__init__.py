# core/views/__init__.py
from .auth import (
    RegisterView, LoginView, LogoutView,
    ForgotPasswordView, ResetPasswordView
)
from .google_auth_views import (
    GoogleLogin, GoogleAuthRedirectView, GoogleAuthCallbackView
)
from .bible import *
from .user import *
from .quiz import *