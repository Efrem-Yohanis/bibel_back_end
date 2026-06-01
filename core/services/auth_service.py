"""
Auth Service - Handles user authentication, registration, session management, and Google OAuth
"""

from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.db import models
from django.core.mail import send_mail
from typing import Optional, Tuple, Dict, Any
import logging
import secrets
from datetime import timedelta
import requests
from urllib.parse import urlencode
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError

from ..models import User, UserSession


logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service for user management"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using Django's make_password"""
        return make_password(password)
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password using Django's check_password"""
        return check_password(password, hashed)
    
    @staticmethod
    def send_mail_message(subject: str, message: str, recipient: str) -> Tuple[bool, Optional[str]]:
        """Send a simple email message."""
        logger.info("Sending email using backend %s", settings.EMAIL_BACKEND)
        logger.info("Email host=%s port=%s use_tls=%s use_ssl=%s", settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_USE_TLS, settings.EMAIL_USE_SSL)
        logger.info("Email from=%s recipient=%s", settings.DEFAULT_FROM_EMAIL, recipient)
        if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend' and not settings.DEBUG:
            logger.error("Console email backend active in production")
            return False, 'Email backend is not configured on production'
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=False)
            logger.info("Email sent successfully to %s", recipient)
            return True, None
        except Exception as e:
            logger.error("Email send failed: %s", str(e), exc_info=True)
            return False, str(e)
    
    def send_email_verification(self, user: User) -> Tuple[Optional[str], Optional[str]]:
        """Generate an email verification link and send it to the user."""
        if not user.email:
            return None, "User does not have an email address"
        try:
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(hours=24)
            user.email_verification_token = token
            user.email_verification_token_expires = expires_at
            user.email_verified = False
            user.save()
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            verify_url = f"{frontend_url}/verify-email?token={token}"
            subject = "Verify your Bible Quiz account"
            message = (
                f"Hello {user.username},\n\n"
                "Thank you for registering with Bible Quiz. Please verify your email address by clicking the link below:\n\n"
                f"{verify_url}\n\n"
                "If you did not register for this account, please ignore this email.\n\n"
                "Blessings,\nBible Quiz Team"
            )
            sent, error = self.send_mail_message(subject, message, user.email)
            if not sent:
                return None, error
            return token, None
        except Exception as e:
            return None, f"Email verification send failed: {str(e)}"
    
    def verify_email(self, token: str) -> Tuple[bool, Optional[str]]:
        """Verify a user's email address using a token."""
        try:
            user = User.objects.get(email_verification_token=token)
            if not user.email_verification_token_expires or user.email_verification_token_expires < timezone.now():
                return False, "Verification token has expired"
            user.email_verified = True
            user.email_verification_token = None
            user.email_verification_token_expires = None
            user.updated_at = timezone.now()
            user.save()
            return True, None
        except User.DoesNotExist:
            return False, "Invalid verification token"
        except Exception as e:
            return False, f"Email verification failed: {str(e)}"
    
    def send_password_reset_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """Generate a password reset token and send a reset link to the user's email."""
        try:
            user = User.objects.get(email=email)
            if user.auth_provider == 'google':
                return False, "Password reset is only available for non-Google accounts"
            reset_token, error = self.set_password_reset_token(email)
            if error:
                return False, error
            frontend_url = settings.FRONTEND_URL.rstrip('/')
            reset_url = f"{frontend_url}/reset-password?token={reset_token}"
            subject = "Bible Quiz password reset request"
            message = (
                f"Hello {user.username},\n\n"
                "We received a request to reset your password. Click the link below to choose a new password:\n\n"
                f"{reset_url}\n\n"
                "If you did not request a password reset, you can ignore this message.\n\n"
                "Blessings,\nBible Quiz Team"
            )
            sent, error = self.send_mail_message(subject, message, user.email)
            if not sent:
                return False, error
            return True, None
        except User.DoesNotExist:
            return False, "User with that email does not exist"
        except Exception as e:
            return False, f"Password reset email send failed: {str(e)}"
    
    def register_user(self, username: str, password: str, email: str = None) -> Tuple[Optional[User], Optional[str]]:
        """Register a new user"""
        try:
            # Check if username exists
            if User.objects.filter(username=username).exists():
                return None, "Username already exists"
            
            # Check if email exists
            if email and User.objects.filter(email=email).exists():
                return None, "Email already registered"
            
            # Create user
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                created_at=timezone.now(),
                updated_at=timezone.now(),
                is_active=True,
                is_admin=False,
                auth_provider='email',
                email_verified=False
            )
            
            return user, None
            
        except Exception as e:
            return None, f"Registration failed: {str(e)}"
    
    def login_user(self, username_or_email: str, password: str, ip_address: str = None, user_agent: str = None) -> Tuple[Optional[Dict], Optional[str]]:
        """Login user and create session"""
        try:
            # Find user by username or email
            user = User.objects.filter(
                models.Q(username=username_or_email) | models.Q(email=username_or_email)
            ).first()
            
            if not user:
                return None, "Invalid username/email or password"
            
            if not user.is_active:
                return None, "Account is deactivated"
            if user.auth_provider != 'google' and user.email and not user.email_verified:
                return None, "Email address not verified. Please verify your email before logging in"
            
            if not check_password(password, user.password):
                return None, "Invalid username/email or password"
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Create session for tracking
            session_token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(days=30)
            
            UserSession.objects.create(
                user=user,
                token=session_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True
            )
            
            # Update last login
            user.last_login = timezone.now()
            user.updated_at = timezone.now()
            user.save()
            
            return {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'session_token': session_token,
                'expires_at': expires_at,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin
            }, None
            
        except Exception as e:
            return None, f"Login failed: {str(e)}"
    
    def google_login(self, access_token: str = None, id_token: str = None, 
                     ip_address: str = None, user_agent: str = None) -> Tuple[Optional[Dict], Optional[str]]:
        """Handle Google OAuth2 login"""
        try:
            user_info = None
            
            # If id_token is provided, verify it with Google
            if id_token:
                verification_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
                response = requests.get(verification_url)
                
                if response.status_code != 200:
                    return None, "Invalid Google ID token"
                
                user_info = response.json()
            
            # If access_token is provided, get user info from Google
            elif access_token:
                userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
                headers = {'Authorization': f'Bearer {access_token}'}
                response = requests.get(userinfo_url, headers=headers)
                
                if response.status_code != 200:
                    return None, "Invalid Google access token"
                
                user_info = response.json()
            
            else:
                return None, "No token provided"
            
            email = user_info.get('email')
            google_id = user_info.get('id') or user_info.get('sub')
            first_name = user_info.get('given_name', '')
            last_name = user_info.get('family_name', '')
            
            if not email:
                return None, "Email not provided by Google"
            
            # Check if user already exists
            user = self.get_user_by_email(email)
            is_new_user = False
            
            if user:
                # Link Google ID if not already linked
                if not user.google_id:
                    user.google_id = google_id
                    user.auth_provider = 'google'
                user.email_verified = True
                user.save()
            else:
                # Create new user
                username = email.split('@')[0]
                # Ensure username is unique
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{secrets.token_hex(4)}"
                
                user = User.objects.create(
                    username=username,
                    email=email,
                    password=make_password(secrets.token_urlsafe(12)),
                    google_id=google_id,
                    auth_provider='google',
                    email_verified=True,
                    first_name=first_name,
                    last_name=last_name,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                    is_active=True,
                    is_admin=False
                )
                is_new_user = True
            
            if not user.is_active:
                return None, "Account is deactivated"
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Create session
            session_token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(days=30)
            
            UserSession.objects.create(
                user=user,
                token=session_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True
            )
            
            # Update last login
            user.last_login = timezone.now()
            user.updated_at = timezone.now()
            user.save()
            
            return {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'session_token': session_token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'is_new_user': is_new_user
            }, None
            
        except Exception as e:
            return None, f"Google login failed: {str(e)}"
    
    def get_google_auth_url(self) -> Tuple[Optional[Dict], Optional[str]]:
        """Get Google OAuth2 authorization URL"""
        try:
            google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
            
            params = {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'response_type': 'code',
                'scope': 'email profile',
                'access_type': 'online',
                'prompt': 'select_account',
            }
            
            auth_url = f"{google_auth_url}?{urlencode(params)}"
            
            return {'auth_url': auth_url}, None
            
        except Exception as e:
            return None, f"Failed to generate auth URL: {str(e)}"
    
    def handle_google_callback(self, code: str, ip_address: str = None, 
                               user_agent: str = None) -> Tuple[Optional[Dict], Optional[str]]:
        """Handle Google OAuth2 callback and exchange code for tokens"""
        try:
            # Exchange code for access token
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code',
            }
            
            token_response = requests.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                return None, "Failed to exchange authorization code"
            
            token_info = token_response.json()
            access_token = token_info.get('access_token')
            
            if not access_token:
                return None, "No access token received"
            
            # Use the access token to login
            return self.google_login(access_token=access_token, ip_address=ip_address, user_agent=user_agent)
            
        except Exception as e:
            return None, f"Callback handling failed: {str(e)}"
    
    def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Find a user by their Google account ID"""
        try:
            return User.objects.get(google_id=google_id)
        except User.DoesNotExist:
            return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address"""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None
    
    def link_google_account(self, user_id: int, google_id: str, provider: str = 'google') -> Tuple[bool, Optional[str]]:
        """Link an existing user account to a Google account"""
        try:
            user = User.objects.get(id=user_id)
            user.google_id = google_id
            user.auth_provider = provider
            user.updated_at = timezone.now()
            user.save()
            return True, None
        except Exception as e:
            return False, f"Linking Google account failed: {str(e)}"
    
    def set_password_reset_token(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate and store a password reset token for a user"""
        try:
            user = User.objects.get(email=email)
            if user.auth_provider == 'google':
                return None, "Password reset is unavailable for Google-authenticated accounts"
            reset_token = secrets.token_urlsafe(24)
            expires_at = timezone.now() + timedelta(hours=1)
            
            user.reset_token = reset_token
            user.reset_token_expires = expires_at
            user.updated_at = timezone.now()
            user.save()
            
            return reset_token, None
            
        except User.DoesNotExist:
            return None, "User with that email does not exist"
        except Exception as e:
            return None, f"Password reset token generation failed: {str(e)}"
    
    def reset_password(self, reset_token: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """Reset a user's password using a valid reset token"""
        try:
            user = User.objects.get(reset_token=reset_token)
            
            if not user.reset_token_expires or user.reset_token_expires < timezone.now():
                return False, "Reset token has expired"
            
            user.password = make_password(new_password)
            user.reset_token = None
            user.reset_token_expires = None
            user.updated_at = timezone.now()
            user.save()
            
            return True, None
            
        except User.DoesNotExist:
            return False, "Invalid or expired reset token"
        except Exception as e:
            return False, f"Password reset failed: {str(e)}"
    
    def logout_user(self, token: str) -> Tuple[bool, Optional[str]]:
        """Logout user by deactivating session"""
        try:
            session = UserSession.objects.filter(token=token, is_active=True).first()
            if session:
                session.is_active = False
                session.save()
                return True, None
            return False, "Session not found"
        except Exception as e:
            return False, f"Logout failed: {str(e)}"
    
    def get_user_profile(self, user_id: int) -> Tuple[Optional[User], Optional[str]]:
        """Get user profile by ID"""
        try:
            user = User.objects.get(id=user_id, is_active=True)
            return user, None
        except User.DoesNotExist:
            return None, "User not found"
    
    def update_user_profile(self, user_id: int, username: str = None, email: str = None) -> Tuple[Optional[User], Optional[str]]:
        """Update user profile"""
        try:
            user = User.objects.get(id=user_id)
            
            if username:
                if User.objects.exclude(id=user_id).filter(username=username).exists():
                    return None, "Username already taken"
                user.username = username
            
            if email:
                if User.objects.exclude(id=user_id).filter(email=email).exists():
                    return None, "Email already registered"
                user.email = email
            
            user.updated_at = timezone.now()
            user.save()
            
            return user, None
            
        except User.DoesNotExist:
            return None, "User not found"
        except Exception as e:
            return None, f"Update failed: {str(e)}"
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """Change user password"""
        try:
            user = User.objects.get(id=user_id)
            
            if not check_password(old_password, user.password):
                return False, "Old password is incorrect"
            
            user.password = make_password(new_password)
            user.updated_at = timezone.now()
            user.save()
            
            return True, None
            
        except User.DoesNotExist:
            return False, "User not found"
        except Exception as e:
            return False, f"Password change failed: {str(e)}"
    
    def validate_token(self, token: str) -> Tuple[Optional[User], Optional[str]]:
        """Validate user authentication token.

        Supports both JWT access tokens and legacy session tokens.
        """
        try:
            print(f"Validating token: {token[:20]}...")
            
            # If the token looks like a JWT, validate it with SimpleJWT.
            if token.count('.') == 2:
                try:
                    access_token = AccessToken(token)
                except TokenError as e:
                    print(f"JWT validation failed: {str(e)}")
                    return None, "Invalid or expired token"

                user_id = access_token.get('user_id')
                if not user_id:
                    print("JWT token missing user_id")
                    return None, "Invalid token payload"

                user = User.objects.filter(id=user_id, is_active=True).first()
                if not user:
                    print("User not found for JWT token")
                    return None, "User not found"

                print(f"JWT token valid for user: {user.username}")
                return user, None

            # Fallback: support legacy session tokens stored in UserSession.
            session = UserSession.objects.filter(
                token=token,
                is_active=True,
                expires_at__gt=timezone.now()
            ).select_related('user').first()

            if not session:
                print("Session not found or expired")
                return None, "Invalid or expired token"

            if not session.user.is_active:
                print("User is inactive")
                return None, "User account is inactive"

            print(f"Session token valid for user: {session.user.username}")
            return session.user, None
            
        except Exception as e:
            print(f"Token validation error: {str(e)}")
            return None, f"Token validation failed: {str(e)}"