from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Create an admin user if it does not exist'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='admin', help='Admin username')
        parser.add_argument('--email', type=str, default='admin@example.com', help='Admin email')
        parser.add_argument('--password', type=str, default='StrongPass123!', help='Admin password')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{username}" already exists')
            )
            user = User.objects.get(username=username)
            if not user.is_admin:
                user.is_admin = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated "{username}" to admin')
                )
            return

        # Create new admin user
        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            user.is_admin = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user "{username}"')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create admin user: {str(e)}')
            )
