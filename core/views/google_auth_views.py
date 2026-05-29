"""
Google OAuth2 Authentication Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.conf import settings
from django.shortcuts import redirect
import requests
from urllib.parse import urlencode

from ..models import User


class GoogleLogin(SocialLoginView):
    """
    Google OAuth2 login endpoint.
    Accepts an access_token from Google and returns JWT tokens.
    """
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = settings.GOOGLE_REDIRECT_URI


class GoogleAuthRedirectView(APIView):
    """
    Get Google OAuth2 redirect URL.
    Frontend can redirect users to this URL for Google login.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
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
        
        return Response({
            'status': 'success',
            'auth_url': auth_url,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'client_id': settings.GOOGLE_CLIENT_ID,
        })


class GoogleAuthCallbackView(APIView):
    """
    Handle Google OAuth2 callback.
    Exchange authorization code for access token and user info.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Handle GET request from Google OAuth redirect"""
        code = request.GET.get('code')
        error = request.GET.get('error')
        
        # Your frontend URL - Lovable app
        FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'https://bibel-quiz-christan-felloship.lovable.app')
        
        if error:
            return redirect(f"{FRONTEND_URL}/login?error={error}")
        
        if not code:
            return redirect(f"{FRONTEND_URL}/login?error=no_code")
        
        # Exchange code for tokens
        result = self.exchange_code_for_tokens(code)
        
        if result.get('error'):
            return redirect(f"{FRONTEND_URL}/login?error={result['error']}")
        
        # Get full name from Google (temporary, not stored in DB)
        google_full_name = result.get('google_full_name', result['user']['username'])
        
        # Redirect to frontend with tokens in URL (no first_name/last_name)
        redirect_url = (
            f"{FRONTEND_URL}/?"
            f"access_token={result['access_token']}&"
            f"refresh_token={result['refresh_token']}&"
            f"user_id={result['user']['id']}&"
            f"username={result['user']['username']}&"
            f"email={result['user']['email']}&"
            f"display_name={google_full_name}&"
            f"is_new_user={result['is_new_user']}"
        )
        
        return redirect(redirect_url)
    
    def post(self, request):
        """Handle POST request from frontend"""
        code = request.data.get('code')
        
        if not code:
            return Response({
                'status': 'error',
                'message': 'Authorization code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = self.exchange_code_for_tokens(code)
        
        if result.get('error'):
            return Response({
                'status': 'error',
                'message': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)
    
    def exchange_code_for_tokens(self, code):
        """Exchange authorization code for access token and user info"""
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        }
        
        try:
            token_response = requests.post(token_url, data=token_data)
            
            if token_response.status_code != 200:
                error_msg = token_response.json().get('error_description', 'Failed to exchange authorization code')
                return {'error': error_msg}
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            # Get user info from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(userinfo_url, headers=headers)
            
            if user_response.status_code != 200:
                return {'error': 'Failed to get user information'}
            
            user_data = user_response.json()
            
            # Extract Google user data
            email = user_data.get('email')
            google_id = user_data.get('id')
            google_full_name = user_data.get('name', '')
            
            # Create username from email (remove domain and special chars)
            if not email:
                return {'error': 'Email not provided by Google'}
            
            base_username = email.split('@')[0]
            # Clean username (remove special characters)
            base_username = ''.join(c for c in base_username if c.isalnum() or c == '_')
            
            # Check if user exists by email
            user = None
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                pass
            
            # If not found by email, try google_id
            if not user and google_id:
                try:
                    user = User.objects.get(google_id=google_id)
                except User.DoesNotExist:
                    pass
            
            created = False
            
            if user:
                # Update existing user with google_id if not already set
                updated = False
                if not user.google_id and google_id:
                    user.google_id = google_id
                    updated = True
                if user.auth_provider != 'google':
                    user.auth_provider = 'google'
                    updated = True
                if updated:
                    user.save()
            else:
                # Create new user - ensure username is unique
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create user with ONLY fields that exist in your User model
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None,  # No password for Google auth users
                    google_id=google_id,
                    auth_provider='google',
                    is_active=True
                )
                created = True
            
            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            # Return user data (only fields from your model)
            return {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                },
                'google_full_name': google_full_name,  # Temporary, not stored in DB
                'is_new_user': created
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e)}