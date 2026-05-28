import os
import sys
import django
import re
from pathlib import Path
from typing import Dict, List

# Make sure the project root is on sys.path so `bibel_project` can be imported
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
# Initialize Django
django.setup()

from django.db import transaction
from core.models import Book, Language, Chapter, Verse, VerseText


def parse_genesis_text(text_content: str) -> Dict[int, List[Dict]]:
    """Parse the Genesis text and return a dict of chapters -> list of verses.

    Accepts lines like:
      Chapter 1
      1 - In the beginning...
      2 - And the earth...
    """
    chapters = {}
    current_chapter = None
    current_verses = []

    lines = text_content.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Chapter heading (case-insensitive)
        m = re.match(r'(?i)^chapter\s+(\d+)', line)
        if m:
            if current_chapter is not None and current_verses:
                chapters[current_chapter] = current_verses
            current_chapter = int(m.group(1))
            current_verses = []
            continue

        # Verse lines: try formats "1 - text", "1. text", "1) text", or "1 text"
        m = re.match(r'^(\d+)\s*[-\.)]?\s*(.+)$', line)
        if m and current_chapter is not None:
            verse_num = int(m.group(1))
            verse_text = m.group(2).strip()
            current_verses.append({'number': verse_num, 'text': verse_text})
            continue

        # Skip headers like "Book: Genesis (GEN)" or separators

    # Add last chapter
    if current_chapter is not None and current_verses:
        chapters[current_chapter] = current_verses

    return chapters


def load_text_file(filepath: Path) -> str:
    with filepath.open('r', encoding='utf-8') as fh:
        return fh.read()


def insert_genesis_from_file(file_path: str = None):
    project_root = Path(__file__).resolve().parent.parent
    default_path = project_root / 'bibel_txt' / 'old' / 'en' / 'Genesis.txt'

    path = Path(file_path) if file_path else default_path

    print('=' * 60)
    print('INSERTING GENESIS (ENGLISH)')
    print('=' * 60)

    if not path.exists():
        print(f"ERROR: Genesis text file not found at {path}")
        return

    text = load_text_file(path)
    chapters_data = parse_genesis_text(text)

    if not chapters_data:
        print('No chapters parsed from the file. Please check format.')
        return

    try:
        book = Book.objects.get(name__iexact='Genesis')
    except Book.DoesNotExist:
        print("ERROR: Book 'Genesis' not found. Create the book first.")
        return

    try:
        language = Language.objects.get(code='en')
    except Language.DoesNotExist:
        print("ERROR: Language with code 'en' not found. Create languages first.")
        return

    print(f"Found book: {book.name} (id={book.id})")
    print(f"Using language: {language.name} (code={language.code})")
    print(f"Parsed {len(chapters_data)} chapters from {path.name}")

    inserted = 0
    updated = 0

    with transaction.atomic():
        for ch_num in sorted(chapters_data.keys()):
            verses = chapters_data[ch_num]
            chapter, created = Chapter.objects.get_or_create(
                book=book,
                chapter_number=ch_num,
                defaults={'total_verses': len(verses)}
            )

            if created:
                inserted += 1
                print(f"Created Chapter {ch_num}")
            else:
                chapter.total_verses = len(verses)
                chapter.save()
                updated += 1
                print(f"Updated Chapter {ch_num} (already existed)")

            vcount = 0
            for v in verses:
                verse_obj, vcreated = Verse.objects.get_or_create(
                    chapter=chapter,
                    verse_number=v['number']
                )

                vt, tc = VerseText.objects.get_or_create(
                    verse=verse_obj,
                    language=language,
                    defaults={'text': v['text']}
                )

                if not tc:
                    vt.text = v['text']
                    vt.save()

                vcount += 1

            print(f"  Inserted/updated {vcount} verses for Chapter {ch_num}")

        # Update book metadata after all inserts
        book.total_chapters = book.chapters.count()
        book.has_audio = book.has_audio  # leave unchanged
        book.save()

    print('\n' + '=' * 60)
    print('Genesis import complete')
    print(f'Total chapters processed: {len(chapters_data)}')
    print(f'Chapters created: {inserted}, chapters updated: {updated}')
    print(f'Total verses for book: {Verse.objects.filter(chapter__book=book).count()}')
    print('=' * 60)


if __name__ == '__main__':
    insert_genesis_from_file()
