"""
Custom authentication for Bearer tokens
"""

from rest_framework import authentication
from rest_framework import exceptions
from .services.auth_service import AuthService

class BearerAuthentication(authentication.BaseAuthentication):
    """Bearer token authentication"""
    
    def authenticate(self, request):
        # Get the authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        print(f"=== DEBUG AUTH ===")
        print(f"Auth header from META: {auth_header[:50] if auth_header else 'None'}")
        print(f"All headers: {dict(request.headers)}")
        
        if not auth_header:
            # Also check the headers dictionary
            auth_header = request.headers.get('Authorization', '')
            print(f"Auth header from headers: {auth_header[:50] if auth_header else 'None'}")
        
        if not auth_header:
            print("No authorization header found")
            return None
        
        # Check if it's a Bearer token
        parts = auth_header.split()
        
        if len(parts) != 2:
            print(f"Invalid header format: {len(parts)} parts")
            return None
        
        if parts[0].lower() != 'bearer':
            print(f"Invalid scheme: {parts[0]}")
            return None
        
        token = parts[1]
        print(f"Token extracted: {token[:30]}...")
        
        # Validate the token
        auth_service = AuthService()
        user, error = auth_service.validate_token(token)
        
        if error:
            print(f"Validation error: {error}")
            raise exceptions.AuthenticationFailed(error)
        
        if not user:
            print("No user found for token")
            raise exceptions.AuthenticationFailed('User not found')
        
        print(f"Authentication successful for user: {user.username}")
        return (user, token)
    
    def authenticate_header(self, request):
        return 'Bearer'