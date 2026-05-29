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
            'auth_url': auth_url
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
        
        # Get frontend URL from settings or use default
        FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'https://bibel-quiz.onrender.com')
        
        if error:
            # Redirect to frontend login with error
            return redirect(f"{FRONTEND_URL}/login?error={error}")
        
        if not code:
            return redirect(f"{FRONTEND_URL}/login?error=no_code")
        
        # Exchange code for tokens
        result = self.exchange_code_for_tokens(code)
        
        if result.get('error'):
            return redirect(f"{FRONTEND_URL}/login?error={result['error']}")
        
        # Redirect to frontend home page with tokens in URL
        # Frontend will read these and store in localStorage
        redirect_url = (
            f"{FRONTEND_URL}/?"
            f"access_token={result['access_token']}&"
            f"refresh_token={result['refresh_token']}&"
            f"user_id={result['user']['id']}&"
            f"username={result['user']['username']}&"
            f"email={result['user']['email']}&"
            f"first_name={result['user']['first_name']}&"
            f"last_name={result['user']['last_name']}&"
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
        # Exchange code for access token
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
                return {'error': 'Failed to exchange authorization code'}
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            # Get user info from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(userinfo_url, headers=headers)
            
            if user_response.status_code != 200:
                return {'error': 'Failed to get user information'}
            
            user_data = user_response.json()
            
            # Create or update user
            email = user_data.get('email')
            google_id = user_data.get('id')
            first_name = user_data.get('given_name', '')
            last_name = user_data.get('family_name', '')
            
            # Check if user exists
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': first_name,
                    'last_name': last_name,
                    'google_id': google_id,
                    'auth_provider': 'google',
                    'is_active': True
                }
            )
            
            if not created and not user.google_id:
                user.google_id = google_id
                user.auth_provider = 'google'
                user.save()
            
            # Generate JWT tokens
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)
            
            return {
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
                'is_new_user': created
            }
            
        except Exception as e:
            return {'error': str(e)}