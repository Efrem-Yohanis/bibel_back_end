"""
Setup Database and Create Admin User - Standalone Script
Runs migrations and creates admin user with pure Python
"""

import os
import sys
import django
import subprocess

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from django.core.management import call_command
from core.models import User


def run_migrations():
    """Run Django migrations"""
    print("[MIGRATIONS] Running database migrations...")
    try:
        call_command('migrate', verbosity=2)
        print("✓ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        return False


def create_admin_user(username='admin', email='admin@example.com', password='StrongPass123!'):
    """Create admin user"""
    print(f"\n[ADMIN USER] Creating admin user '{username}'...")
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        if not user.is_admin:
            user.is_admin = True
            user.save()
            print(f"✓ Updated '{username}' to admin status")
        else:
            print(f"✓ Admin user '{username}' already exists")
        return True
    
    # Create new admin user
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        user.is_admin = True
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
    
    parser = argparse.ArgumentParser(description='Setup database and create admin user')
    parser.add_argument('--username', default='admin', help='Admin username (default: admin)')
    parser.add_argument('--email', default='admin@example.com', help='Admin email')
    parser.add_argument('--password', default='StrongPass123!', help='Admin password')
    
    args = parser.parse_args()
    
    # Run migrations first
    migrations_ok = run_migrations()
    if not migrations_ok:
        sys.exit(1)
    
    # Then create admin user
    success = create_admin_user(
        username=args.username,
        email=args.email,
        password=args.password
    )
    
    print("\n" + "="*60)
    print("SETUP COMPLETE")
    print("="*60)
    
    sys.exit(0 if success else 1)
