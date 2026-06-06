#!/usr/bin/env python3
"""
Insert verse texts into EXISTING books in the Django DB.

Unlike insert_scraped_book.py, this script:
  - Does NOT delete/recreate the Book record (preserves testament, bible_order, etc.)
  - Finds the book by name (case-insensitive) OR creates it if missing
  - For each chapter in the JSON, gets-or-creates the Chapter row
  - For each verse, gets-or-creates the Verse row
  - Creates or updates the VerseText for the given language

Usage (single file):
    python insert_verses_into_existing_books.py <json-file> <book-name> <language-code>

Usage (directory — all .json files):
    python insert_verses_into_existing_books.py <json-directory> <language-code>

The book-name must match the name stored in the DB (case-insensitive).
Example:
    python insert_verses_into_existing_books.py 1_corinthians.json "1ኛ ቆሮንቶስ" am
    python insert_verses_into_existing_books.py scripts/nt_books/ am
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

import django

# ── Django setup ────────────────────────────────────────────────────────────
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from django.db import transaction
from core.models import Book, Chapter, Language, Verse, VerseText


# ── Helpers (same logic as the original script) ─────────────────────────────

def parse_chapter_number(chapter_title: str) -> int:
    if not chapter_title:
        return 1
    match = re.search(r'(?:ምዕራፍ|chapter)\s*(\d+)', chapter_title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'^(\d+)$', chapter_title.strip())
    if match:
        return int(match.group(1))
    return 1


def load_json(path: str) -> Dict[str, Any]:
    encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1']
    last_error = None
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        except json.JSONDecodeError:
            raise
    raise UnicodeDecodeError(
        f"Could not decode {path} with any supported encoding", b'', 0, 1, str(last_error)
    )


def normalize_verses_data(data: Dict[str, Any]) -> Dict[int, List[Dict[str, Any]]]:
    """Return {chapter_number: [verse_dict, ...]}"""
    if 'chapters' in data:
        chapters = data['chapters']
        chapter_map: Dict[int, List] = {}

        if isinstance(chapters, dict):
            for chapter_key, chapter_value in chapters.items():
                try:
                    chapter_num = int(chapter_key)
                except Exception:
                    continue
                verses = chapter_value.get('verses', []) if isinstance(chapter_value, dict) else []
                chapter_map[chapter_num] = verses
            return chapter_map

        if isinstance(chapters, list):
            for chapter_value in chapters:
                if not isinstance(chapter_value, dict):
                    continue
                chapter_num = chapter_value.get('chapter')
                if chapter_num is None:
                    chapter_num = parse_chapter_number(chapter_value.get('title', ''))
                try:
                    chapter_num = int(chapter_num)
                except Exception:
                    continue
                verses = chapter_value.get('verses', [])
                if isinstance(verses, list):
                    chapter_map[chapter_num] = verses
            return chapter_map

    if 'verses' in data and isinstance(data['verses'], list):
        chapter_num = parse_chapter_number(data.get('chapter_title', ''))
        return {chapter_num: data['verses']}

    raise ValueError('Unsupported JSON format: expected root keys "chapters" or "verses"')


def format_book_name_from_filename(path: Path) -> str:
    stem = path.stem
    parts = stem.split('_')
    formatted_parts = [part if part.isdigit() else part.capitalize() for part in parts]
    return ' '.join(formatted_parts)


# ── Core insert logic ────────────────────────────────────────────────────────

def insert_verses_into_existing_book(
    file_path: str,
    book_name: str,
    language_code: str,
    overwrite: bool = True,
):
    """
    Load JSON and insert/update VerseText rows for an EXISTING book.

    Parameters
    ----------
    file_path     : path to the JSON file
    book_name     : exact (case-insensitive) name of the Book in the DB
    language_code : e.g. 'am', 'en'
    overwrite     : if True, existing VerseText rows are updated; otherwise skipped
    """
    data = load_json(file_path)
    chapters_data = normalize_verses_data(data)

    # ── Resolve language ────────────────────────────────────────────────────
    language, lang_created = Language.objects.get_or_create(
        code=language_code,
        defaults={'name': language_code, 'native_name': language_code},
    )
    if lang_created:
        print(f'  Created new language: {language.code}')
    else:
        print(f'  Using language: {language.code}')

    # ── Resolve book ────────────────────────────────────────────────────────
    try:
        book = Book.objects.get(name__iexact=book_name)
        print(f'  Found existing book: "{book.name}" (pk={book.pk}, order={book.bible_order})')
    except Book.DoesNotExist:
        print(f'  ⚠️  Book "{book_name}" NOT found in DB. Skipping.')
        print(f'       Available books (first 20):')
        for b in Book.objects.order_by('bible_order')[:20]:
            print(f'         pk={b.pk} order={b.bible_order} name="{b.name}"')
        return
    except Book.MultipleObjectsReturned:
        books = Book.objects.filter(name__iexact=book_name)
        print(f'  ⚠️  Multiple books named "{book_name}" found:')
        for b in books:
            print(f'       pk={b.pk} order={b.bible_order}')
        print('       Please fix duplicates first. Skipping.')
        return

    # ── Insert data ─────────────────────────────────────────────────────────
    total_verses_inserted = 0
    total_verses_updated = 0
    total_verses_skipped = 0

    with transaction.atomic():
        for chapter_number in sorted(chapters_data.keys()):
            verses_raw = chapters_data[chapter_number]

            # Build de-duplicated verse map  {verse_num: text}
            verse_map: Dict[int, str] = {}
            duplicates: Dict[int, int] = {}
            for verse_data in verses_raw:
                verse_num = verse_data.get('verse')
                if verse_num is None:
                    continue
                text_val = verse_data.get('text', '').strip()
                if verse_num in verse_map:
                    duplicates[verse_num] = duplicates.get(verse_num, 1) + 1
                verse_map[verse_num] = text_val

            if not verse_map:
                print(f'  Chapter {chapter_number}: no verses found, skipping.')
                continue

            # Get or create Chapter
            chapter_obj, ch_created = Chapter.objects.get_or_create(
                book=book,
                chapter_number=chapter_number,
                defaults={'total_verses': len(verse_map)},
            )
            if not ch_created and chapter_obj.total_verses != len(verse_map):
                chapter_obj.total_verses = len(verse_map)
                chapter_obj.save(update_fields=['total_verses'])

            ch_status = 'created' if ch_created else 'existing'
            print(f'  Chapter {chapter_number} ({ch_status}): {len(verse_map)} unique verses', end='')
            if duplicates:
                print(f'  [duplicates merged: {sorted(duplicates.keys())}]', end='')
            print()

            for verse_num, text_val in sorted(verse_map.items()):
                # Get or create Verse
                verse_obj, _ = Verse.objects.get_or_create(
                    chapter=chapter_obj,
                    verse_number=verse_num,
                )

                # Get or create / update VerseText
                vt, vt_created = VerseText.objects.get_or_create(
                    verse=verse_obj,
                    language=language,
                    defaults={'text': text_val},
                )
                if vt_created:
                    total_verses_inserted += 1
                elif overwrite and vt.text != text_val:
                    vt.text = text_val
                    vt.save(update_fields=['text'])
                    total_verses_updated += 1
                else:
                    total_verses_skipped += 1

        # Update book.total_chapters to reflect actual DB count
        actual_chapter_count = Chapter.objects.filter(book=book).count()
        if book.total_chapters != actual_chapter_count:
            book.total_chapters = actual_chapter_count
            book.save(update_fields=['total_chapters'])

    print(f'  ✅ Done — inserted: {total_verses_inserted}, '
          f'updated: {total_verses_updated}, skipped: {total_verses_skipped}')


# ── Directory import ─────────────────────────────────────────────────────────

# Map JSON filename stems → DB book names for the New Testament (Amharic).
# Edit / extend this table to match your actual DB book names.
NT_FILENAME_TO_DB_NAME: Dict[str, str] = {
    # Gospels
    '1_matthew':        'ማቴዎስ',
    'matthew':          'ማቴዎስ',
    '2_mark':           'ማርቆስ',
    'mark':             'ማርቆስ',
    '3_luke':           'ሉቃስ',
    'luke':             'ሉቃስ',
    '4_john':           'ዮሐንስ',
    'john':             'ዮሐንስ',
    # Acts
    '5_acts':           'የሐዋርያት ሥራ',
    'acts':             'የሐዋርያት ሥራ',
    # Paul's letters
    '6_romans':         'ሮሜ',
    'romans':           'ሮሜ',
    '7_1_corinthians':  '1ኛ ቆሮንቶስ',
    '1_corinthians':    '1ኛ ቆሮንቶስ',
    '8_2_corinthians':  '2ኛ ቆሮንቶስ',
    '2_corinthians':    '2ኛ ቆሮንቶስ',
    '9_galatians':      'ገላትያ',
    'galatians':        'ገላትያ',
    '10_ephesians':     'ኤፌሶን',
    'ephesians':        'ኤፌሶን',
    '11_philippians':   'ፊልጵስዩስ',
    'philippians':      'ፊልጵስዩስ',
    '12_colossians':    'ቆላስይስ',
    'colossians':       'ቆላስይስ',
    '13_1_thessalonians': '1ኛ ተሰሎንቄ',
    '1_thessalonians':  '1ኛ ተሰሎንቄ',
    '14_2_thessalonians': '2ኛ ተሰሎንቄ',
    '2_thessalonians':  '2ኛ ተሰሎንቄ',
    '15_1_timothy':     '1ኛ ጢሞቴዎስ',
    '1_timothy':        '1ኛ ጢሞቴዎስ',
    '16_2_timothy':     '2ኛ ጢሞቴዎስ',
    '2_timothy':        '2ኛ ጢሞቴዎስ',
    '17_titus':         'ቲቶ',
    'titus':            'ቲቶ',
    '18_philemon':      'ፊልሞና',
    'philemon':         'ፊልሞና',
    '19_hebrews':       'ዕብራውያን',
    'hebrews':          'ዕብራውያን',
    # General letters
    '20_james':         'ያዕቆብ',
    'james':            'ያዕቆብ',
    '21_1_peter':       '1ኛ ጴጥሮስ',
    '1_peter':          '1ኛ ጴጥሮስ',
    '22_2_peter':       '2ኛ ጴጥሮስ',
    '2_peter':          '2ኛ ጴጥሮስ',
    '23_1_john':        '1ኛ ዮሐንስ',
    '1_john':           '1ኛ ዮሐንስ',
    '24_2_john':        '2ኛ ዮሐንስ',
    '2_john':           '2ኛ ዮሐንስ',
    '25_3_john':        '3ኛ ዮሐንስ',
    '3_john':           '3ኛ ዮሐንስ',
    '26_jude':          'ይሁዳ',
    'jude':             'ይሁዳ',
    '27_revelation':    'ራእይ',
    'revelation':       'ራእይ',
}


def import_directory(directory_path: str, language_code: str):
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f'Directory not found: {directory_path}')

    json_files = sorted(directory.glob('*.json'))
    if not json_files:
        print(f'No JSON files found in {directory_path}')
        return

    for json_file in json_files:
        stem = json_file.stem.lower()

        # Try to look up the DB name from the mapping table
        db_name = NT_FILENAME_TO_DB_NAME.get(stem)
        if db_name is None:
            # Fall back to the formatted filename (works if DB name matches)
            db_name = format_book_name_from_filename(json_file)
            print(f'\n{"="*80}')
            print(f'⚠️  "{json_file.name}" not in mapping table — '
                  f'trying "{db_name}" as the book name.')
        else:
            print(f'\n{"="*80}')
            print(f'Importing "{json_file.name}" → book "{db_name}"')

        try:
            insert_verses_into_existing_book(str(json_file), db_name, language_code)
        except Exception as exc:
            print(f'  ❌ Failed: {exc}')


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) == 3 and Path(sys.argv[1]).is_dir():
        # Directory mode
        import_directory(sys.argv[1], sys.argv[2])

    elif len(sys.argv) == 4:
        # Single-file mode
        json_file, book_name, language_code = sys.argv[1], sys.argv[2], sys.argv[3]
        print(f'Importing "{json_file}" → book "{book_name}" [{language_code}]')
        insert_verses_into_existing_book(json_file, book_name, language_code)

    else:
        print('Usage:')
        print('  Single file:')
        print('    python insert_verses_into_existing_books.py <json-file> <book-name> <language-code>')
        print('  Directory (uses NT_FILENAME_TO_DB_NAME mapping):')
        print('    python insert_verses_into_existing_books.py <json-directory> <language-code>')
        print()
        print('Examples:')
        print('  python insert_verses_into_existing_books.py 1_corinthians.json "1ኛ ቆሮንቶስ" am')
        print('  python insert_verses_into_existing_books.py scripts/nt_books/ am')
        sys.exit(1)