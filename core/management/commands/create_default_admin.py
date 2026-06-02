from django.core.management.base import BaseCommand
import os
import secrets


class Command(BaseCommand):
    help = 'Create or update default admin user (for production deployment)'

    def handle(self, *args, **options):
        from core.models import User

        email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
        username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
        password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'StrongPass123!')
        first = os.environ.get('DEFAULT_ADMIN_FIRST_NAME', 'Admin')
        last = os.environ.get('DEFAULT_ADMIN_LAST_NAME', 'User')

        user = User.objects.filter(email=email).first()
        if not user:
            if User.objects.filter(username=username).exists():
                suffix = 1
                candidate = username
                while User.objects.filter(username=candidate).exists():
                    candidate = f"{username}{suffix}"
                    suffix += 1
                username = candidate

            user = User.objects.create(
                username=username,
                email=email,
                first_name=first,
                last_name=last,
                is_admin=True,
                is_active=True,
            )
            created = True
        else:
            created = False

        user.set_password(password)
        user.is_admin = True
        user.is_active = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin user: {email} (username={user.username})'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Updated admin user: {email} (username={user.username})'))
