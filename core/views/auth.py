"""
Auth Views - Authentication and user management endpoints
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import logging

from ..services.auth_service import AuthService
from ..models import User
from ..serializers.auth_serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer,
    EmailVerificationSerializer, TokenResponseSerializer
)

auth_service = AuthService()
logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """User registration endpoint"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user account",
        operation_summary="User Registration",
        tags=['Authentication'],
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response('User created successfully', RegisterSerializer),
            400: 'Validation error'
        }
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user, error = auth_service.register_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email')
        )
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'message': 'User registered successfully.',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login endpoint"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login user and get access token",
        operation_summary="User Login",
        tags=['Authentication'],
        request_body=LoginSerializer,
        responses={
            200: TokenResponseSerializer,
            401: 'Invalid credentials'
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result, error = auth_service.login_user(
            username_or_email=data['username_or_email'],
            password=data['password'],
            ip_address=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR')),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Logout user and invalidate token",
        operation_summary="User Logout",
        tags=['Authentication'],
        responses={
            200: 'Logout successful',
            400: 'Logout failed'
        }
    )
    def post(self, request):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        
        success, error = auth_service.logout_user(token)
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    """Request password reset"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Request password reset email",
        operation_summary="Forgot Password",
        tags=['Authentication'],
        request_body=ForgotPasswordSerializer,
        responses={200: 'Password reset email sent'}
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success, error = auth_service.send_password_reset_email(
            email=serializer.validated_data['email']
        )
        
        if error:
            if error == 'User with that email does not exist':
                return Response({
                    'status': 'success',
                    'message': 'If an account with that email exists, a password reset request has been received.'
                }, status=status.HTTP_200_OK)
            if error == 'Password reset is only available for non-Google accounts':
                return Response({
                    'status': 'error',
                    'message': error
                }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'status': 'error',
                'message': 'Password reset request failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'status': 'success',
            'message': 'If an account with that email exists, a password reset request has been received.'
        }, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    """Reset password using token"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Reset password using token",
        operation_summary="Reset Password",
        tags=['Authentication'],
        request_body=ResetPasswordSerializer,
        responses={200: 'Password reset successful'}
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        success, error = auth_service.reset_password(
            reset_token=data['token'],
            new_password=data['new_password']
        )
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)


class VerifyEmailView(APIView):
    """Verify email address using a token"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Verify an email address with a token",
        operation_summary="Verify Email",
        tags=['Authentication'],
        request_body=EmailVerificationSerializer,
        responses={200: 'Email verified successfully', 400: 'Invalid token'}
    )
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success, error = auth_service.verify_email(
            token=serializer.validated_data['token']
        )
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)


class SendVerificationCodeView(APIView):
    """Resend email verification code to user"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Resend verification email to user",
        operation_summary="Resend Verification Email",
        tags=['Authentication'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
            },
            required=['email']
        ),
        responses={
            200: 'Verification email sent',
            404: 'User not found',
            500: 'Email send failed'
        }
    )
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'status': 'error',
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # No email verification is required in this app flow.
        # Respond success so the frontend can continue without email delivery.
        return Response({
            'status': 'success',
            'message': 'Verification is not required. Please continue.'
        }, status=status.HTTP_200_OK)


class GoogleLoginView(APIView):
    """Google OAuth2 login endpoint"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login or register using Google OAuth2 token",
        operation_summary="Google Login",
        tags=['Authentication'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'access_token': openapi.Schema(type=openapi.TYPE_STRING, description='Google OAuth2 access token'),
                'id_token': openapi.Schema(type=openapi.TYPE_STRING, description='Google ID token (alternative)'),
            },
            required=['access_token']
        ),
        responses={
            200: TokenResponseSerializer,
            400: 'Invalid token'
        }
    )
    def post(self, request):
        access_token = request.data.get('access_token')
        id_token = request.data.get('id_token')
        
        if not access_token and not id_token:
            return Response({
                'status': 'error',
                'message': 'Either access_token or id_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use the auth service to handle Google login
        result, error = auth_service.google_login(
            access_token=access_token,
            id_token=id_token,
            ip_address=request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR')),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)


class GoogleAuthRedirectView(APIView):
    """Get Google OAuth2 redirect URL"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get Google OAuth2 authorization URL",
        operation_summary="Google Auth Redirect",
        tags=['Authentication'],
        responses={
            200: openapi.Response('Auth URL generated'),
        }
    )
    def get(self, request):
        result, error = auth_service.get_google_auth_url()
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)


class GoogleAuthCallbackView(APIView):
    """Handle Google OAuth2 callback"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Handle Google OAuth2 callback and exchange code for tokens",
        operation_summary="Google Auth Callback",
        tags=['Authentication'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='Authorization code from Google'),
            },
            required=['code']
        ),
        responses={
            200: TokenResponseSerializer,
            400: 'Invalid code'
        }
    )
    def post(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({
                'status': 'error',
                'message': 'Authorization code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result, error = auth_service.handle_google_callback(code)
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)