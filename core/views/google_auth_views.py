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
    
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({
                'status': 'error',
                'message': 'Authorization code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
                return Response({
                    'status': 'error',
                    'message': 'Failed to exchange authorization code'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            # Get user info from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {'Authorization': f'Bearer {access_token}'}
            user_response = requests.get(userinfo_url, headers=headers)
            
            if user_response.status_code != 200:
                return Response({
                    'status': 'error',
                    'message': 'Failed to get user information'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user_data = user_response.json()
            
            # Create or update user
            email = user_data.get('email')
            google_id = user_data.get('id')
            name = user_data.get('name', '')
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
            
            return Response({
                'status': 'success',
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
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)