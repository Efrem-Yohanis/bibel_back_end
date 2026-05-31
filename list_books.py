import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from core.models import Book

# Get all book names
books = Book.objects.values_list('name', flat=True).order_by('name')
print("Books in database:")
for book in books:
    print(f"  - {book}")
