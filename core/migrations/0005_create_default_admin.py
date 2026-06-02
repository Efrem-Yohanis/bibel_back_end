from django.db import migrations


def noop(apps, schema_editor):
    # Empty migration - admin user creation is handled by management command
    # to allow production-only deployment without affecting local development
    pass


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('core', '0004_add_email_verification_fields'),
    ]

    operations = [
        migrations.RunPython(noop, noop),
    ]
