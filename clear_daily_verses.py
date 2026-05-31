import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from core.models import DailyVerse, DailyVerseCategory

# Clear existing data
DailyVerse.objects.all().delete()
DailyVerseCategory.objects.all().delete()

print("✅ Cleared all daily verses and categories")
