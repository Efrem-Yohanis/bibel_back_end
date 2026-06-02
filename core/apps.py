import os
import logging

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.contrib.auth.hashers import make_password

logger = logging.getLogger(__name__)


def create_default_admin(sender, **kwargs):
    try:
        from .models import User

        email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
        username = os.environ.get('DEFAULT_ADMIN_USERNAME', 'admin')
        password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'StrongPass123!')
        first = os.environ.get('DEFAULT_ADMIN_FIRST_NAME', 'Admin')
        last = os.environ.get('DEFAULT_ADMIN_LAST_NAME', 'User')

        user = User.objects.filter(email=email).first()
        if user:
            logger.info('Default admin already exists: %s', email)
            if not user.check_password(password) or not user.is_admin or not user.is_active:
                user.password = make_password(password)
                user.is_admin = True
                user.is_active = True
                user.first_name = first
                user.last_name = last
                user.save()
                logger.info('Updated default admin account: %s', email)
            return

        original_username = username
        suffix = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{suffix}"
            suffix += 1

        User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            first_name=first,
            last_name=last,
            is_admin=True,
            is_active=True,
        )
        logger.info('Created default admin user: %s (username=%s)', email, username)
    except Exception as exc:
        logger.exception('Failed to create default admin user: %s', exc)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        post_migrate.connect(create_default_admin, sender=self)
