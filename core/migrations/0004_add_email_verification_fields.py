from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_dailyversecategory_dailyverse'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verification_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='email_verification_token_expires',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
