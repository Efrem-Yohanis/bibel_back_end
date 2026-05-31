import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from core.models import Book, Chapter, Verse, DailyVerse

# Test parsing a few verse references
test_verses = [
    "Genesis 28:15",
    "Psalm 4:5",
    "Psalms 4:5",
    "Proverbs 3:5-6",
    "1 Chronicles 22:13",
    "Matthew 14:27",
]

BOOK_NAME_MAP = {
    'Psalm': 'Psalms',
}

for verse_ref in test_verses:
    print(f"\nTesting: {verse_ref}")
    
    parts = verse_ref.split()
    
    if len(parts) == 3:
        book_name = f"{parts[0]} {parts[1]}"
        verse_info = parts[2]
    elif len(parts) == 2:
        book_name = parts[0]
        verse_info = parts[1]
    else:
        print(f"  ❌ Invalid format")
        continue
    
    # Apply mapping
    if book_name in BOOK_NAME_MAP:
        book_name = BOOK_NAME_MAP[book_name]
    
    print(f"  Book: {book_name}, Verse Info: {verse_info}")
    
    # Parse chapter:verse
    if ":" in verse_info:
        chapter_str, verse_str = verse_info.split(":")
        chapter_num = int(chapter_str)
        
        if "-" in verse_str:
            verse_num = int(verse_str.split("-")[0])
        else:
            verse_num = int(verse_str)
    else:
        print(f"  ❌ No ':' found in verse info")
        continue
    
    print(f"  Chapter: {chapter_num}, Verse: {verse_num}")
    
    # Try to find verse
    try:
        book = Book.objects.get(name=book_name)
        print(f"  ✓ Book found: {book.name}")
        
        chapter = Chapter.objects.get(book=book, chapter_number=chapter_num)
        print(f"  ✓ Chapter found: {chapter}")
        
        verse = Verse.objects.get(chapter=chapter, verse_number=verse_num)
        print(f"  ✓ Verse found: {verse}")
        
    except Book.DoesNotExist:
        print(f"  ❌ Book not found: {book_name}")
    except Chapter.DoesNotExist:
        print(f"  ❌ Chapter not found: {book_name} {chapter_num}")
    except Verse.DoesNotExist:
        print(f"  ❌ Verse not found: {book_name} {chapter_num}:{verse_num}")

print(f"\n\nTotal DailyVerses in database: {DailyVerse.objects.count()}")
