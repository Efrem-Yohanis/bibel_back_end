# insert_genesis_amharic_fixed.py
import os
import sys
import django
import re
from pathlib import Path
from typing import Dict, List

# Setup Django
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from django.db import transaction
from core.models import Book, Language, Chapter, Verse, VerseText


def parse_amharic_genesis(text_content: str) -> Dict[int, List[Dict]]:
    """Parse Amharic Genesis text format"""
    
    chapters = {}
    current_chapter = None
    current_verses = []
    
    lines = text_content.splitlines()
    
    # Debug: Print first few lines to see format
    print("\n📄 First 20 lines of file:")
    for i, line in enumerate(lines[:20]):
        print(f"   Line {i+1}: {line[:100]}...")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Look for chapter numbers
        # Format could be: "ምዕራፍ 1" or just "1" or "Chapter 1"
        chapter_match = re.match(r'^(?:ምዕራፍ|Chapter)\s+(\d+)', line, re.IGNORECASE)
        
        if chapter_match:
            # Save previous chapter
            if current_chapter is not None and current_verses:
                chapters[current_chapter] = current_verses
                current_verses = []
            
            current_chapter = int(chapter_match.group(1))
            print(f"   Found chapter: {current_chapter}")
            continue
        
        # Also check for standalone numbers that might be chapters
        if not current_chapter and re.match(r'^\d+$', line):
            num = int(line)
            if 1 <= num <= 50:
                if current_chapter is not None and current_verses:
                    chapters[current_chapter] = current_verses
                    current_verses = []
                current_chapter = num
                print(f"   Found chapter (standalone): {current_chapter}")
                continue
        
        # Look for verse numbers
        # Amharic might have: "1. text" or "1 - text" or "1 text"
        verse_match = re.match(r'^(\d+)\s*[\.\-)]?\s*(.+)$', line)
        
        if verse_match and current_chapter is not None:
            verse_num = int(verse_match.group(1))
            verse_text = verse_match.group(2).strip()
            
            # Validate verse number is reasonable (1-200)
            if 1 <= verse_num <= 200:
                current_verses.append({
                    'number': verse_num,
                    'text': verse_text
                })
            continue
        
        # If line doesn't match and we're in a chapter, it might be continuation of last verse
        if current_chapter is not None and current_verses and not verse_match:
            # Add to last verse
            current_verses[-1]['text'] += ' ' + line
    
    # Save last chapter
    if current_chapter is not None and current_verses:
        chapters[current_chapter] = current_verses
    
    return chapters


def insert_amharic_genesis(file_path: str = None):
    """Insert Amharic Genesis into database"""
    
    project_root = Path(__file__).resolve().parent.parent
    
    # Try to find the Amharic Genesis file
    possible_paths = [
        file_path,
        str(project_root / 'bibel_txt' / 'old' / 'am' / 'GEN_ኦሪት_ዘፍጥረት.txt'),
        str(project_root / 'bibel_txt' / 'old' / 'am' / 'Genesis_am.txt'),
        str(project_root / 'bibel_txt' / 'old' / 'am' / '1_genesis.txt'),
    ]
    
    file_to_use = None
    for path in possible_paths:
        if path and Path(path).exists():
            file_to_use = Path(path)
            break
    
    if not file_to_use:
        print("❌ Genesis Amharic text file not found!")
        print("   Searched in:")
        for path in possible_paths:
            print(f"     - {path}")
        return
    
    print("=" * 60)
    print("📖 INSERTING GENESIS (AMHARIC)")
    print("=" * 60)
    
    # Read file
    with open(file_to_use, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Parse the text
    chapters_data = parse_amharic_genesis(text)
    
    if not chapters_data:
        print("\n❌ No chapters parsed from the file.")
        print("   Please check the file format.")
        print("\n💡 Expected format example:")
        print("   ምዕራፍ 1")
        print("   1 - በመጀመሪያ እግዚአብሔር ሰማይንና ምድርን ፈጠረ።")
        print("   2 - ምድርም ባዶ ነበረች...")
        return
    
    # Get Genesis book
    book = Book.objects.filter(name__iexact='Genesis').first()
    if not book:
        print("❌ Book 'Genesis' not found!")
        return
    
    # Get Amharic language
    try:
        language = Language.objects.get(code='am')
    except Language.DoesNotExist:
        print("❌ Language 'am' not found!")
        return
    
    print(f"\n✅ Book: {book.name} (id={book.id})")
    print(f"✅ Language: {language.name} (code={language.code})")
    print(f"✅ Parsed {len(chapters_data)} chapters")
    
    # Show which chapters were found
    print(f"\n📊 Chapters found: {sorted(chapters_data.keys())}")
    
    # Insert data
    print("\n💾 Inserting into database...")
    
    with transaction.atomic():
        for ch_num in sorted(chapters_data.keys()):
            verses = chapters_data[ch_num]
            
            # Get or create chapter
            chapter, created = Chapter.objects.get_or_create(
                book=book,
                chapter_number=ch_num,
                defaults={'total_verses': len(verses)}
            )
            
            if created:
                print(f"\n✅ Created Chapter {ch_num}")
            else:
                print(f"\n🔄 Updating Chapter {ch_num}")
            
            # Insert verses
            for verse_data in verses:
                verse, v_created = Verse.objects.get_or_create(
                    chapter=chapter,
                    verse_number=verse_data['number']
                )
                
                verse_text, t_created = VerseText.objects.get_or_create(
                    verse=verse,
                    language=language,
                    defaults={'text': verse_data['text']}
                )
                
                if not t_created:
                    verse_text.text = verse_data['text']
                    verse_text.save()
            
            print(f"   📖 {len(verses)} verses inserted")
    
    # Update book info
    book.total_chapters = Book.objects.get(id=book.id).chapters.count()
    book.save()
    
    # Verify
    total_verses = Verse.objects.filter(chapter__book=book).count()
    
    print("\n" + "=" * 60)
    print("✅ GENESIS (AMHARIC) IMPORT COMPLETE!")
    print(f"   Chapters: {book.total_chapters}")
    print(f"   Total verses: {total_verses}")
    print(f"   Amharic verses: {VerseText.objects.filter(language=language, verse__chapter__book=book).count()}")
    print("=" * 60)


def check_amharic_file_content():
    """Check the content of the Amharic file to debug"""
    
    project_root = Path(__file__).resolve().parent.parent
    file_path = project_root / 'bibel_txt' / 'old' / 'am' / 'GEN_ኦሪት_ዘፍጥረት.txt'
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print("=" * 60)
    print("🔍 CHECKING AMHARIC FILE CONTENT")
    print("=" * 60)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n📄 Total lines: {len(lines)}")
    print("\n📝 First 50 lines:")
    print("-" * 40)
    
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d}: {line.rstrip()[:100]}")
    
    print("\n🔍 Looking for chapter markers...")
    chapter_lines = []
    for i, line in enumerate(lines, 1):
        if 'ምዕራፍ' in line or re.match(r'^\s*\d+\s*$', line.strip()):
            chapter_lines.append((i, line.strip()))
    
    print(f"\n📖 Found {len(chapter_lines)} potential chapter markers:")
    for line_num, line in chapter_lines[:20]:
        print(f"   Line {line_num}: {line}")


if __name__ == "__main__":
    # First, check the file content
    check_amharic_file_content()
    
    # Then insert
    print("\n" + "=" * 60)
    response = input("Continue with insertion? (yes/no): ")
    if response.lower() == 'yes':
        insert_amharic_genesis()
    else:
        print("Cancelled.")