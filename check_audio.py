#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from core.models import ChapterAudio, Book, BookAudio

print("=== Audio Data Summary ===")
print(f"BookAudio records: {BookAudio.objects.count()}")
print(f"ChapterAudio records: {ChapterAudio.objects.count()}")

print("\n=== ChapterAudio by Language ===")
for lang_code in ['en', 'am', 'or', 'ti']:
    count = ChapterAudio.objects.filter(language__code=lang_code, is_available=True).count()
    print(f"{lang_code}: {count} chapter audios")

print("\n=== 1 Chronicles Audio (Book ID=125) ===")
book = Book.objects.get(id=125)
print(f"Book: {book.name}")
print(f"Book.has_audio field: {book.has_audio}")

# Check English
en_count = ChapterAudio.objects.filter(
    book=book,
    language__code='en',
    is_available=True
).count()
print(f"English chapter audios: {en_count}")

# Check Amharic
am_count = ChapterAudio.objects.filter(
    book=book,
    language__code='am',
    is_available=True
).count()
print(f"Amharic chapter audios: {am_count}")

print("\n=== BookAudio for 1 Chronicles ===")
ba = BookAudio.objects.filter(book=book, language__code='en').first()
print(f"English BookAudio: {ba}")
ba_am = BookAudio.objects.filter(book=book, language__code='am').first()
print(f"Amharic BookAudio: {ba_am}")

print("\n=== Books with any audio ===")
books_with_audio = ChapterAudio.objects.values('book__name').distinct().count()
print(f"Books with ChapterAudio: {books_with_audio}")
print("\nFirst 10 books with Amharic audio:")
books_list = ChapterAudio.objects.filter(
    language__code='am'
).values('book__name', 'book__id').distinct().order_by('book__id')[:10]
for b in books_list:
    print(f"  - {b['book__name']} (ID: {b['book__id']})")

print("\n=== Sample ChapterAudio record ===")
sample = ChapterAudio.objects.first()
if sample:
    print(f"Book: {sample.book.name}")
    print(f"Chapter: {sample.chapter_number}")
    print(f"Language: {sample.language.code}")
    print(f"Audio URL: {sample.audio_url[:60]}..." if sample.audio_url else "None")
    print(f"Duration: {sample.duration}")
    print(f"Is Available: {sample.is_available}")
