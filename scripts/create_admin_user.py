"""
Create Admin User - Standalone Script
Directly creates an admin user in the database without Django management commands
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from core.models import User


def create_admin_user(username='admin', email='admin@example.com', password='StrongPass123!'):
    """Create or update admin user."""

    user = User.objects.filter(username=username).first()
    if not user and email:
        user = User.objects.filter(email=email).first()

    if user:
        updated = False
        if user.username != username and not User.objects.filter(username=username).exclude(pk=user.pk).exists():
            user.username = username
            updated = True
        if user.email != email:
            user.email = email
            updated = True
        if not user.is_admin:
            user.is_admin = True
            updated = True
        if not user.is_active:
            user.is_active = True
            updated = True
        user.set_password(password)
        updated = True
        user.save()
        print(f"✓ Updated existing user to admin: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Password: {password}")
        return True

    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        user.is_admin = True
        user.is_active = True
        user.save()
        print(f"✓ Successfully created admin user '{username}'")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        return True
    except Exception as e:
        print(f"✗ Failed to create admin user: {str(e)}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Create admin user')
    parser.add_argument('--username', default='admin', help='Admin username (default: admin)')
    parser.add_argument('--email', default='admin@example.com', help='Admin email')
    parser.add_argument('--password', default='StrongPass123!', help='Admin password')
    
    args = parser.parse_args()
    
    success = create_admin_user(
        username=args.username,
        email=args.email,
        password=args.password
    )
    
    sys.exit(0 if success else 1)
