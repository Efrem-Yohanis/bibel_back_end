from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = 'Create or update default admin user (for production deployment)'

    def handle(self, *args, **options):
        from core.models import User

        # Production defaults (use env vars to override if needed)
        email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'StrongPass123!')
        first = os.environ.get('DEFAULT_ADMIN_FIRST_NAME', 'Admin')
        last = os.environ.get('DEFAULT_ADMIN_LAST_NAME', 'User')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first,
                'last_name': last,
                'is_admin': True,
                'is_active': True,
            }
        )

        user.set_password(password)
        user.is_admin = True
        user.is_active = True
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin user: {email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Updated admin user: {email}'))
