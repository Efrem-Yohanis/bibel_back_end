# scripts/simple_reimport.py
#!/usr/bin/env python
"""
Simple re-import of Bible data
Run: python scripts/simple_reimport.py
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')

import django
django.setup()

from core.models import Language, Book, Testament, Chapter, Verse, VerseText
from django.db import transaction

SOURCE_DB = Path('/home/efrem/bibel/app/bible_quiz.db')

def clean_testaments():
    """Clean up testaments first"""
    print("Cleaning testaments...")
    # Delete all except Old and New
    Testament.objects.exclude(name__in=['Old', 'New']).delete()
    
    # Ensure Old and New exist
    old, _ = Testament.objects.get_or_create(name='Old')
    new, _ = Testament.objects.get_or_create(name='New')
    print(f"  Testaments: Old (id={old.id}), New (id={new.id})")
    return old, new

def clean_all_data():
    """Clear all Bible data"""
    print("\nClearing existing Bible data...")
    VerseText.objects.all().delete()
    Verse.objects.all().delete()
    Chapter.objects.all().delete()
    # Don't delete books, just clear them
    Book.objects.all().delete()
    print("  Cleared all Bible data")

def reimport_bible():
    print("=" * 60)
    print("📖 RE-IMPORTING BIBLE DATA")
    print("=" * 60)
    
    # First clean testaments
    old_test, new_test = clean_testaments()
    
    # Clear existing data
    clean_all_data()
    
    conn = sqlite3.connect(str(SOURCE_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get languages
    languages = {lang.code: lang for lang in Language.objects.all()}
    print(f"\n📍 Languages: {list(languages.keys())}")
    
    # Get unique books from source
    print("\n📚 Importing books...")
    cursor.execute("""
        SELECT DISTINCT b.name, t.name as testament_name
        FROM books b
        JOIN testaments t ON b.testament_id = t.id
        ORDER BY t.name, b.name
    """)
    
    books = cursor.fetchall()
    book_map = {}
    
    for book in books:
        testament = old_test if book['testament_name'] == 'Old' else new_test
        obj = Book.objects.create(
            name=book['name'],
            testament=testament
        )
        book_map[book['name']] = obj
        print(f"  Created book: {book['name']} ({book['testament_name']})")
    
    # Import chapters
    print("\n📑 Importing chapters...")
    cursor.execute("""
        SELECT DISTINCT b.name as book_name, c.chapter_number
        FROM chapters c
        JOIN books b ON c.book_id = b.id
        ORDER BY b.name, c.chapter_number
    """)
    
    chapters = cursor.fetchall()
    chapter_map = {}
    
    for ch in chapters:
        book = book_map.get(ch['book_name'])
        if book:
            obj = Chapter.objects.create(
                book=book,
                chapter_number=ch['chapter_number']
            )
            chapter_map[(ch['book_name'], ch['chapter_number'])] = obj
    
    print(f"  Created {len(chapters)} chapters")
    
    # Import verses
    print("\n📜 Importing verses...")
    cursor.execute("""
        SELECT DISTINCT b.name as book_name, c.chapter_number, v.verse_number
        FROM verses v
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        ORDER BY b.name, c.chapter_number, v.verse_number
    """)
    
    verses = cursor.fetchall()
    verse_count = 0
    
    for vs in verses:
        chapter = chapter_map.get((vs['book_name'], vs['chapter_number']))
        if chapter:
            Verse.objects.create(
                chapter=chapter,
                verse_number=vs['verse_number']
            )
            verse_count += 1
    
    print(f"  Created {verse_count} verses")
    
    # Import verse texts
    print("\n🌐 Importing verse texts...")
    cursor.execute("""
        SELECT DISTINCT b.name as book_name, c.chapter_number, v.verse_number, 
               l.code as language_code, vt.text
        FROM verse_texts vt
        JOIN verses v ON vt.verse_id = v.id
        JOIN chapters c ON v.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        JOIN languages l ON vt.language_id = l.id
        WHERE vt.text IS NOT NULL AND vt.text != ''
        ORDER BY b.name, c.chapter_number, v.verse_number, l.code
    """)
    
    texts = cursor.fetchall()
    text_count = 0
    
    for txt in texts:
        chapter = chapter_map.get((txt['book_name'], txt['chapter_number']))
        if chapter:
            verse = Verse.objects.filter(
                chapter=chapter,
                verse_number=txt['verse_number']
            ).first()
            if verse:
                language = languages.get(txt['language_code'])
                if language:
                    VerseText.objects.create(
                        verse=verse,
                        language=language,
                        text=txt['text']
                    )
                    text_count += 1
                    
                    if text_count % 5000 == 0:
                        print(f"    Imported {text_count} verse texts...")
    
    print(f"  Created {text_count} verse texts")
    
    conn.close()
    
    # Final counts
    print("\n" + "=" * 60)
    print("📊 FINAL COUNTS")
    print("=" * 60)
    print(f"  Testaments: {Testament.objects.count()}")
    print(f"  Books: {Book.objects.count()}")
    print(f"  Chapters: {Chapter.objects.count()}")
    print(f"  Verses: {Verse.objects.count()}")
    print(f"  Verse Texts: {VerseText.objects.count()}")
    
    print("\n✅ RE-IMPORT COMPLETE!")

if __name__ == "__main__":
    response = input("\nThis will RE-IMPORT ALL Bible data. Continue? (yes/no): ")
    if response.lower() == 'yes':
        reimport_bible()
    else:
        print("Cancelled.")