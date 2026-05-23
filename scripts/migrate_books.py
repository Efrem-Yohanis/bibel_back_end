#!/usr/bin/env python
"""
Fixed Books Migration Script - Handles duplicates
Run: python scripts/migrate_books_fixed.py
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for Django setup
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup Django environment
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')

import django
django.setup()

from core.models import Language, Book, Testament, Chapter, Verse, VerseText
from django.db import transaction

SOURCE_DB = Path('/home/efrem/bibel/app/bible_quiz.db')

def clear_all_data():
    """Clear existing data before migration"""
    print("\n🗑️ Clearing existing data...")
    VerseText.objects.all().delete()
    Verse.objects.all().delete()
    Chapter.objects.all().delete()
    Book.objects.all().delete()
    Testament.objects.all().delete()
    print("✅ Cleared all data")

def migrate_testaments():
    """Migrate testaments - handle duplicates by using unique names"""
    print("\n📖 Migrating Testaments...")
    
    conn = sqlite3.connect(str(SOURCE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get unique testaments from source
    cursor.execute("SELECT DISTINCT name FROM testaments ORDER BY name")
    testaments = cursor.fetchall()
    
    testament_map = {}
    for testament in testaments:
        obj, created = Testament.objects.get_or_create(
            name=testament['name']
        )
        testament_map[testament['name']] = obj.id
        if created:
            print(f"  ✅ Created testament: {testament['name']}")
        else:
            print(f"  🔄 Found existing testament: {testament['name']}")
    
    conn.close()
    print(f"  📊 Total testaments: {Testament.objects.count()}")
    return testament_map

def migrate_books(testament_map):
    """Migrate books - handle duplicates by using unique names per testament"""
    print("\n📚 Migrating Books...")
    
    conn = sqlite3.connect(str(SOURCE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get unique books with their testament names
    cursor.execute("""
        SELECT DISTINCT b.name, t.name as testament_name
        FROM books b
        JOIN testaments t ON b.testament_id = t.id
        ORDER BY t.name, b.name
    """)
    books = cursor.fetchall()
    
    book_map = {}
    for book in books:
        testament = Testament.objects.get(name=book['testament_name'])
        obj, created = Book.objects.get_or_create(
            name=book['name'],
            testament=testament
        )
        book_map[(book['name'], book['testament_name'])] = obj.id
        if created:
            print(f"  ✅ Created book: {book['name']} ({book['testament_name']})")
        else:
            print(f"  🔄 Found existing book: {book['name']}")
    
    conn.close()
    print(f"  📊 Total books: {Book.objects.count()}")
    return book_map

def migrate_chapters(book_map, testament_map):
    """Migrate chapters - handle duplicates by using unique constraints"""
    print("\n📑 Migrating Chapters...")
    
    conn = sqlite3.connect(str(SOURCE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get unique chapters
    cursor.execute("""
        SELECT DISTINCT b.name as book_name, t.name as testament_name, 
               c.chapter_number
        FROM chapters c
        JOIN books b ON c.book_id = b.id
        JOIN testaments t ON b.testament_id = t.id
        ORDER BY b.name, c.chapter_number
    """)
    chapters = cursor.fetchall()
    
    chapter_map = {}
    count = 0
    for chapter in chapters:
        # Find the book
        book = Book.objects.get(
            name=chapter['book_name'],
            testament__name=chapter['testament_name']
        )
        
        # Create chapter
        obj, created = Chapter.objects.get_or_create(
            book=book,
            chapter_number=chapter['chapter_number']
        )
        
        key = (chapter['book_name'], chapter['testament_name'], chapter['chapter_number'])
        chapter_map[key] = obj.id
        
        count += 1
        if count % 50 == 0:
            print(f"  ✅ Processed {count} chapters...")
    
    conn.close()
    print(f"  📊 Total chapters: {Chapter.objects.count()}")
    return chapter_map

def migrate_verses(chapter_map):
    """Migrate verses"""
    print("\n📜 Migrating Verses...")
    
    conn = sqlite3.connect(str(SOURCE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get verses with their chapter info
    cursor.execute("""
        SELECT DISTINCT b.name as book_name, t.name as testament_name,
               c.chapter_number, v.verse_number
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        JOIN testaments t ON b.testament_id = t.id
        ORDER BY b.name, c.chapter_number, v.verse_number
    """)
    verses = cursor.fetchall()
    
    verse_map = {}
    count = 0
    for verse in verses:
        # Find the chapter
        chapter = Chapter.objects.get(
            book__name=verse['book_name'],
            book__testament__name=verse['testament_name'],
            chapter_number=verse['chapter_number']
        )
        
        # Create verse
        obj, created = Verse.objects.get_or_create(
            chapter=chapter,
            verse_number=verse['verse_number']
        )
        
        key = (verse['book_name'], verse['testament_name'], 
               verse['chapter_number'], verse['verse_number'])
        verse_map[key] = obj.id
        
        count += 1
        if count % 1000 == 0:
            print(f"  ✅ Processed {count} verses...")
    
    conn.close()
    print(f"  📊 Total verses: {Verse.objects.count()}")
    return verse_map

def migrate_verse_texts(verse_map):
    """Migrate verse texts"""
    print("\n🌐 Migrating Verse Texts...")
    
    conn = sqlite3.connect(str(SOURCE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get unique verse texts
    cursor.execute("""
        SELECT DISTINCT b.name as book_name, t.name as testament_name,
               c.chapter_number, v.verse_number, l.code as language_code,
               vt.text
        FROM verse_texts vt
        JOIN verses v ON vt.verse_id = v.id
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        JOIN testaments t ON b.testament_id = t.id
        JOIN languages l ON vt.language_id = l.id
        WHERE vt.text IS NOT NULL AND vt.text != ''
        ORDER BY b.name, c.chapter_number, v.verse_number, l.code
    """)
    verse_texts = cursor.fetchall()
    
    count = 0
    for vt in verse_texts:
        try:
            # Find the verse
            verse = Verse.objects.get(
                chapter__book__name=vt['book_name'],
                chapter__book__testament__name=vt['testament_name'],
                chapter__chapter_number=vt['chapter_number'],
                verse_number=vt['verse_number']
            )
            
            # Find the language
            language = Language.objects.get(code=vt['language_code'])
            
            # Create verse text
            VerseText.objects.update_or_create(
                verse=verse,
                language=language,
                defaults={'text': vt['text']}
            )
            
            count += 1
            if count % 5000 == 0:
                print(f"  ✅ Processed {count} verse texts...")
                
        except Exception as e:
            print(f"  ⚠️ Failed to migrate verse {vt['book_name']} {vt['chapter_number']}:{vt['verse_number']} ({vt['language_code']}): {e}")
    
    conn.close()
    print(f"  📊 Total verse texts: {VerseText.objects.count()}")

def verify_migration():
    """Verify the migration"""
    print("\n" + "=" * 60)
    print("🔍 VERIFYING MIGRATION")
    print("=" * 60)
    
    print(f"\n📊 Statistics:")
    print(f"  Testaments: {Testament.objects.count()}")
    print(f"  Books: {Book.objects.count()}")
    print(f"  Chapters: {Chapter.objects.count()}")
    print(f"  Verses: {Verse.objects.count()}")
    print(f"  Verse Texts: {VerseText.objects.count()}")
    
    # Show books by testament
    print(f"\n📚 Books by Testament:")
    for testament in Testament.objects.all():
        books = Book.objects.filter(testament=testament)
        print(f"  {testament.name}: {books.count()} books")
        if books.count() > 0:
            sample_books = books[:5]
            print(f"    Sample: {', '.join([b.name for b in sample_books])}")
    
    # Show verse texts by language
    print(f"\n🌐 Verse Texts by Language:")
    for language in Language.objects.all():
        count = VerseText.objects.filter(language=language).count()
        print(f"  {language.name} ({language.code}): {count:,} verses")

def test_books_by_language():
    """Test the books/by-language API"""
    print("\n" + "=" * 60)
    print("🧪 TESTING books/by-language")
    print("=" * 60)
    
    from core.services.bible_service import BibleService
    service = BibleService()
    
    for lang in Language.objects.all():
        books = service.get_books_by_language(lang.code)
        print(f"\n  {lang.name} ({lang.code}): {len(books)} books available")
        if books:
            print(f"    First 5: {', '.join([b['name'] for b in books[:5]])}")

@transaction.atomic
def migrate_all():
    """Run all migrations"""
    print("=" * 60)
    print("🚀 MIGRATING BOOKS AND RELATED DATA (FIXED)")
    print("=" * 60)
    
    if not SOURCE_DB.exists():
        print(f"❌ Source database not found at {SOURCE_DB}")
        return False
    
    print(f"✅ Source database found: {SOURCE_DB}")
    
    # Ask if we should clear existing data
    response = input("\nClear existing data before migration? (yes/no): ")
    if response.lower() == 'yes':
        clear_all_data()
    
    try:
        # Migrate in order
        testament_map = migrate_testaments()
        book_map = migrate_books(testament_map)
        chapter_map = migrate_chapters(book_map, testament_map)
        verse_map = migrate_verses(chapter_map)
        migrate_verse_texts(verse_map)
        
        # Verify
        verify_migration()
        test_books_by_language()
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("⚠️  BOOKS MIGRATION TOOL (FIXED VERSION)")
    print("=" * 60)
    print(f"Source: {SOURCE_DB}")
    
    response = input("\nContinue? (yes/no): ")
    
    if response.lower() == 'yes':
        success = migrate_all()
        
        if success:
            print("\n📌 Next steps:")
            print("1. Run: python manage.py runserver 8009")
            print("2. Test: curl 'http://127.0.0.1:8009/api/bible/books/by-language?language=en'")
            print("3. Visit: http://127.0.0.1:8009/swagger/")
    else:
        print("Cancelled.")