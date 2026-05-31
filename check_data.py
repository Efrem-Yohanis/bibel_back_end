import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from core.models import Chapter, Verse, VerseText

# Get stats
total_chapters = Chapter.objects.count()
total_verses = Verse.objects.count()
total_verse_texts = VerseText.objects.count()

print(f"Database Statistics:")
print(f"  Total Chapters: {total_chapters}")
print(f"  Total Verses: {total_verses}")
print(f"  Total Verse Texts: {total_verse_texts}")

# Sample books
from core.models import Book
from django.db.models import Count

books_with_chapters = Book.objects.annotate(chapter_count=Count('chapters')).filter(chapter_count__gt=0).order_by('-chapter_count')[:10]

print(f"\nTop 10 books by chapter count:")
for book in books_with_chapters:
    verse_count = Verse.objects.filter(chapter__book=book).count()
    print(f"  {book.name}: {book.chapter_count} chapters, {verse_count} verses")

# Check Genesis specifically
genesis = Book.objects.get(name='Genesis')
genesis_chapters = genesis.chapters.count()
genesis_verses = Verse.objects.filter(chapter__book=genesis).count()
print(f"\nGenesis specifically: {genesis_chapters} chapters, {genesis_verses} verses")
