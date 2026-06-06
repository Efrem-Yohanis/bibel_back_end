#!/usr/bin/env python3
"""Insert English Bible text files into existing Amharic Book records.

The expected file format is like the files in bibel_txt/new/en:

Book: Matthew (MAT)

Chapter 1
1 - ...
2 - ...

Chapter 2
1 - ...

The script maps English book names to the Amharic DB book names used in this project
and inserts/updates VerseText rows under language code 'en'.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

import django

# Setup Django environment
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from django.db import transaction
from core.models import Book, Chapter, Language, Verse, VerseText

# Mapping from English filename/book name to the Amharic DB book name.
ENGLISH_BOOK_TO_DB_NAME: Dict[str, str] = {
    'matthew': 'ማቴዎስ',
    'mark': 'ማርቆስ',
    'luke': 'ሉቃስ',
    'john': 'ዮሐንስ',
    '1_john': '1ኛ ዮሐንስ',
    '2_john': '2ኛ ዮሐንስ',
    '3_john': '3ኛ ዮሐንስ',
    'acts': 'የሐዋርያት ሥራ',
    'romans': 'ሮሜ',
    '1_corinthians': '1ኛ ቆሮንቶስ',
    '2_corinthians': '2ኛ ቆሮንቶስ',
    'galatians': 'ገላትያ',
    'ephesians': 'ኤፌሶን',
    'philippians': 'ፊልጵስዩስ',
    'colossians': 'ቆላስይስ',
    '1_thessalonians': '1ኛ ተሰሎንቄ',
    '2_thessalonians': '2ኛ ተሰሎንቄ',
    '1_timothy': '1ኛ ጢሞቴዎስ',
    '2_timothy': '2ኛ ጢሞቴዎስ',
    'titus': 'ቲቶ',
    'philemon': 'ፊልሞና',
    'hebrews': 'ዕብራውያን',
    'james': 'ያዕቆብ',
    '1_peter': '1ኛ ጴጥሮስ',
    '2_peter': '2ኛ ጴጥሮስ',
    'jude': 'ይሁዳ',
    'revelation': 'ራዕይ',

    # Old Testament
    'genesis': 'ዘፍጥረት',
    'exodus': 'ዘጸአት',
    'leviticus': 'ዘሌዋውያን',
    'numbers': 'ዘቍጥር',
    'deuteronomy': 'ዘዳግም',
    'joshua': 'ኢያሱ',
    'judges': 'መሳፍንት',
    'ruth': 'ሩት',
    '1_samuel': '1ኛ ሳሙኤል',
    '2_samuel': '2ኛ ሳሙኤል',
    '1_kings': '1ኛ ነገሥት',
    '2_kings': '2ኛ ነገሥት',
    '1_chronicles': '1ኛ ዜና መዋዕል',
    '2_chronicles': '2ኛ ዜና መዋዕል',
    'ezra': 'ዕዝራ',
    'nehemiah': 'ነህምያ',
    'esther': 'አስቴር',
    'job': 'ኢዮብ',
    'psalms': 'መዝሙር',
    'psalm': 'መዝሙር',
    'proverbs': 'ምሳሌ',
    'ecclesiastes': 'መክብብ',
    'song_of_solomon': 'መኃልየ መኃልይ',
    'song_of_songs': 'መኃልየ መኃልይ',
    'isaiah': 'ኢሳይያስ',
    'jeremiah': 'ኤርምያስ',
    'lamentations': 'ሰቆቃወ ኤርምያስ',
    'ezekiel': 'ሕዝቅኤል',
    'daniel': 'ዳንኤል',
    'hosea': 'ሆሴዕ',
    'joel': 'ኢዩኤል',
    'amos': 'አሞጽ',
    'obadiah': 'አብድዩ',
    'jonah': 'ዮናስ',
    'micah': 'ሚክያስ',
    'nahum': 'ናሆም',
    'habakkuk': 'ዕንባቆም',
    'zephaniah': 'ሶፎንያስ',
    'haggai': 'ሐጌ',
    'zechariah': 'ዘካርያስ',
    'malachi': 'ሚልክያስ',
}


def parse_book_name_from_header(text: str) -> str:
    m = re.search(r'^Book:\s*([^\(\n]+)', text, re.IGNORECASE | re.MULTILINE)
    if m:
        return m.group(1).strip()
    return ''


def parse_english_text_file(path: Path) -> Dict[int, List[Dict[str, str]]]:
    text = path.read_text(encoding='utf-8')
    chapters: Dict[int, List[Dict[str, str]]] = {}
    current_chapter = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('===') or line.startswith('---'):
            continue

        chapter_match = re.match(r'(?i)^Chapter\s+(\d+)', line)
        if chapter_match:
            current_chapter = int(chapter_match.group(1))
            chapters[current_chapter] = []
            continue

        verse_match = re.match(r'^(\d+)\s*[-\.)]?\s*(.+)$', line)
        if verse_match and current_chapter is not None:
            verse_number = int(verse_match.group(1))
            verse_text = verse_match.group(2).strip()
            chapters[current_chapter].append({'verse': verse_number, 'text': verse_text})
            continue

    if not chapters:
        raise ValueError('No chapters parsed from this file. Check that it uses "Chapter N" headings and "verse - text" lines.')

    return chapters


def normalize_book_key(name: str) -> str:
    key = name.strip().lower().replace(' ', '_')
    key = re.sub(r'[^a-z0-9_]', '_', key)
    return key


def insert_english_txt(
    file_path: Path,
    db_book_name: str,
    language_code: str = 'en',
    overwrite: bool = True,
    dry_run: bool = False,
):
    chapters_data = parse_english_text_file(file_path)

    language = Language.objects.filter(code=language_code).first()
    if not language:
        if dry_run:
            raise ValueError(
                f'Language "{language_code}" not found in DB. In dry-run mode, the language must already exist.'
            )
        language = Language.objects.create(
            code=language_code,
            name='English',
            native_name='English',
        )
        print(f'Created language: {language.code}')

    try:
        book = Book.objects.get(name__iexact=db_book_name)
    except Book.DoesNotExist:
        raise ValueError(f'Book "{db_book_name}" not found in DB.')
    except Book.MultipleObjectsReturned:
        raise ValueError(f'Multiple books found for "{db_book_name}". Resolve duplicates first.')

    print(f'Using book: {book.name} (pk={book.pk}, order={book.bible_order})')
    print(f'Parsed {len(chapters_data)} chapters from {file_path.name}')

    inserted = 0
    updated = 0
    skipped = 0

    def _do_insert():
        nonlocal inserted, updated, skipped

        for chapter_number in sorted(chapters_data.keys()):
            verses = chapters_data[chapter_number]
            if not verses:
                print(f'  Skipping empty chapter {chapter_number}')
                continue

            chapter_obj, chapter_created = Chapter.objects.get_or_create(
                book=book,
                chapter_number=chapter_number,
                defaults={'total_verses': len(verses)},
            )
            if not chapter_created and chapter_obj.total_verses != len(verses):
                chapter_obj.total_verses = len(verses)
                if not dry_run:
                    chapter_obj.save(update_fields=['total_verses'])

            print(f'  Chapter {chapter_number}: {len(verses)} verses ({"new" if chapter_created else "existing"})')

            for verse in verses:
                verse_obj, _ = Verse.objects.get_or_create(
                    chapter=chapter_obj,
                    verse_number=verse['verse'],
                )
                vt, vt_created = VerseText.objects.get_or_create(
                    verse=verse_obj,
                    language=language,
                    defaults={'text': verse['text']},
                )
                if vt_created:
                    inserted += 1
                elif overwrite and vt.text != verse['text']:
                    if not dry_run:
                        vt.text = verse['text']
                        vt.save(update_fields=['text'])
                    updated += 1
                else:
                    skipped += 1

    if dry_run:
        with transaction.atomic():
            _do_insert()
            transaction.set_rollback(True)
    else:
        with transaction.atomic():
            _do_insert()
            actual_chapters = Chapter.objects.filter(book=book).count()
            if book.total_chapters != actual_chapters:
                book.total_chapters = actual_chapters
                book.save(update_fields=['total_chapters'])

    print(f'\nDone. inserted={inserted}, updated={updated}, skipped={skipped}')


def build_db_book_name(file_path: Path, explicit_name: str = None) -> str:
    if explicit_name:
        return explicit_name

    content = file_path.read_text(encoding='utf-8')
    book_name = parse_book_name_from_header(content)
    if book_name:
        normalized = normalize_book_key(book_name)
        return ENGLISH_BOOK_TO_DB_NAME.get(normalized, book_name)

    stem = normalize_book_key(file_path.stem)
    return ENGLISH_BOOK_TO_DB_NAME.get(stem, file_path.stem)


def _import_directory(
    directory: Path,
    language_code: str,
    overwrite: bool,
    dry_run: bool,
    explicit_book_name: str = None,
):
    txt_files = sorted(directory.glob('*.txt'))
    if not txt_files:
        raise SystemExit(f'No .txt files found in directory: {directory}')

    summary = {
        'processed': 0,
        'skipped': 0,
        'inserted': 0,
        'updated': 0,
        'skipped_rows': 0,
    }

    for txt_file in txt_files:
        print('\n' + '=' * 80)
        print(f'File: {txt_file.name}')
        if explicit_book_name and len(txt_files) == 1:
            db_book_name = explicit_book_name
        else:
            db_book_name = build_db_book_name(txt_file, explicit_book_name)

        print(f'Resolved book name: {db_book_name}')
        try:
            if dry_run:
                with transaction.atomic():
                    insert_english_txt(
                        file_path=txt_file,
                        db_book_name=db_book_name,
                        language_code=language_code,
                        overwrite=overwrite,
                        dry_run=True,
                    )
                    transaction.set_rollback(True)
            else:
                insert_english_txt(
                    file_path=txt_file,
                    db_book_name=db_book_name,
                    language_code=language_code,
                    overwrite=overwrite,
                    dry_run=False,
                )
            summary['processed'] += 1
        except Exception as exc:
            summary['skipped'] += 1
            print(f'  Skipped: {exc}')

    print('\n' + '=' * 80)
    print('Directory import complete')
    print(f"  Processed: {summary['processed']}")
    print(f"  Skipped:   {summary['skipped']}")


def main():
    parser = argparse.ArgumentParser(
        description='Insert English Bible text files into existing Amharic Book records.'
    )
    parser.add_argument('file', help='Path to the English .txt book file or directory.')
    parser.add_argument(
        '--book-name',
        help='Exact DB book name to use for a single file. If omitted, the script maps from the English book title.',
    )
    parser.add_argument('--lang', default='en', help='Language code to insert (default: en).')
    parser.add_argument('--no-overwrite', action='store_true', help='Do not update existing VerseText values.')
    parser.add_argument('--dry-run', action='store_true', help='Parse and show what would be inserted without writing.')
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        raise SystemExit(f'File or directory not found: {file_path}')

    if file_path.is_dir():
        print(f'Importing all .txt files from directory: {file_path}')
        _import_directory(
            directory=file_path,
            language_code=args.lang,
            overwrite=not args.no_overwrite,
            dry_run=args.dry_run,
            explicit_book_name=args.book_name,
        )
        return

    db_book_name = build_db_book_name(file_path, args.book_name)
    print(f'Inserting file: {file_path.name}')
    print(f'Resolved book name: {db_book_name}')

    try:
        insert_english_txt(
            file_path=file_path,
            db_book_name=db_book_name,
            language_code=args.lang,
            overwrite=not args.no_overwrite,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        raise SystemExit(f'Error: {exc}')


if __name__ == '__main__':
    main()
