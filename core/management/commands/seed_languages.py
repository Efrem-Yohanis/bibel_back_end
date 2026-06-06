"""
Management command to seed required languages into the database.
Run: python manage.py seed_languages
Safe to run multiple times (idempotent).
"""

from django.core.management.base import BaseCommand
from core.models import Language


class Command(BaseCommand):
    help = "Seed required languages (en, am, or, ti) into the database"

    def handle(self, *args, **options):
        languages_data = [
            {'code': 'en', 'name': 'English', 'native_name': 'English'},
            {'code': 'am', 'name': 'Amharic', 'native_name': 'አማርኛ'},
            {'code': 'or', 'name': 'Afaan Oromo', 'native_name': 'Afaan Oromo'},
            {'code': 'ti', 'name': 'Tigrinya', 'native_name': 'ትግርኛ'},
        ]

        for lang_data in languages_data:
            language, created = Language.objects.get_or_create(
                code=lang_data['code'],
                defaults={
                    'name': lang_data['name'],
                    'native_name': lang_data['native_name'],
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Created language: {language.name} ({language.code})")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⏭️  Language already exists: {language.name} ({language.code})")
                )

        # Print summary
        total = Language.objects.count()
        active = Language.objects.filter(is_active=True).count()
        self.stdout.write(
            self.style.SUCCESS(f"\n✅ Language seeding complete! Total: {total}, Active: {active}")
        )
