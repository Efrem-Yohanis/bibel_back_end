from django.db import migrations


def create_default_admin(apps, schema_editor):
    """Auto-create default admin user on first migration."""
    User = apps.get_model('core', 'User')
    
    # Check if admin already exists
    if User.objects.filter(email='admin@example.com').exists():
        return
    
    # Create the admin user
    user = User.objects.create_user(
        email='admin@example.com',
        password='StrongPass123!',
        first_name='Admin',
        last_name='User'
    )
    user.is_admin = True
    user.is_active = True
    user.save()


def remove_admin(apps, schema_editor):
    """Reverse: remove the auto-created admin user."""
    User = apps.get_model('core', 'User')
    User.objects.filter(email='admin@example.com').delete()


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('core', '0004_add_email_verification_fields'),
    ]

    operations = [
        migrations.RunPython(create_default_admin, remove_admin),
    ]
