"""
Auth Service - Handles user authentication, registration, and session management
"""

from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.db import models
from typing import Optional, Tuple, Dict, Any
import secrets
from datetime import timedelta
from ..models import User, UserSession


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
                auth_provider='email'
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
            
            if not check_password(password, user.password):
                return None, "Invalid username/email or password"
            
            # Generate token
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(days=30)
            
            # Store session
            session = UserSession.objects.create(
                user=user,
                token=token,
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
                'access_token': token,
                'token_type': 'bearer',
                'expires_at': expires_at,
                'user_id': user.id,
                'username': user.username,
                'is_admin': user.is_admin
            }, None
            
        except Exception as e:
            return None, f"Login failed: {str(e)}"
    
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
    
    def create_google_user(self, username: str, email: str, google_id: str, provider: str = 'google') -> Tuple[Optional[User], Optional[str], Optional[str]]:
        """Create a new user account for a Google-authenticated user"""
        try:
            # Check if email exists
            if email and User.objects.filter(email=email).exists():
                return None, None, "Email already registered"
            
            # Check if username exists
            if User.objects.filter(username=username).exists():
                # Append random number to username
                username = f"{username}_{secrets.token_hex(4)}"
            
            # Create user with random password (they will use Google login)
            random_password = secrets.token_urlsafe(12)
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(random_password),
                google_id=google_id,
                auth_provider=provider,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                is_active=True,
                is_admin=False
            )
            
            return user, random_password, None
            
        except Exception as e:
            return None, None, f"Google user creation failed: {str(e)}"
    
    def set_password_reset_token(self, email: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate and store a password reset token for a user"""
        try:
            user = User.objects.get(email=email)
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
        """Validate user session token"""
        try:
            # Debug: Print token being validated
            print(f"Validating token: {token[:20]}...")
            
            # Check if token exists and is active
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
            
            print(f"Token valid for user: {session.user.username}")
            return session.user, None
            
        except Exception as e:
            print(f"Token validation error: {str(e)}")
            return None, f"Token validation failed: {str(e)}"