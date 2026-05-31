"""
Authentication Serializers - Matching Pydantic schemas
"""

from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from ..models import User


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration"""
    username = serializers.CharField(max_length=50, min_length=3)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)
    confirm_password = serializers.CharField(write_only=True, min_length=6, max_length=128)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def validate(self, data):
        # Only validate password confirmation if confirm_password is provided
        if 'confirm_password' in data and data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    user_agent = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at', 'updated_at', 
                  'last_login', 'is_active', 'is_admin', 'preferred_language',
                  'total_quizzes_taken', 'total_correct_answers', 
                  'total_questions_answered']
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login', 
                           'total_quizzes_taken', 'total_correct_answers', 
                           'total_questions_answered']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request"""
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset"""
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification"""
    token = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""
    access_token = serializers.CharField()
    token_type = serializers.CharField(default='bearer')
    expires_at = serializers.DateTimeField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    is_admin = serializers.BooleanField()