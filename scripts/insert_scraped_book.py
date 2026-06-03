#!/usr/bin/env python3
"""Insert scraped Bible chapter JSON into the Django DB."""

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import django

# Setup Django environment
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')
django.setup()

from django.db import transaction
from core.models import Book, Chapter, Language, Verse, VerseText


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
    raise UnicodeDecodeError(f"Could not decode JSON file {path} with supported encodings", b'', 0, 1, str(last_error))


def normalize_verses_data(data: Dict[str, Any]) -> Dict[int, List[Dict[str, Any]]]:
    if 'chapters' in data:
        chapters = data['chapters']
        chapter_map = {}

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


def insert_scraped_book(file_path: str, book_name: str, language_code: str):
    data = load_json(file_path)
    chapters = normalize_verses_data(data)

    books_to_delete = Book.objects.filter(name__iexact=book_name)
    if books_to_delete.exists():
        count = books_to_delete.count()
        books_to_delete.delete()
        print(f'Deleted {count} existing book(s) named "{book_name}"')

    book = Book.objects.create(
        name=book_name,
        bible_order=0,
        total_chapters=0,
    )
    print(f'Created book: {book.name} (id={book.id})')

    language, lang_created = Language.objects.get_or_create(
        code=language_code,
        defaults={'name': language_code, 'native_name': language_code}
    )
    if lang_created:
        print(f'Created language: {language.code}')
    else:
        print(f'Using existing language: {language.code}')

    with transaction.atomic():
        for chapter_number in sorted(chapters.keys()):
            verses = chapters[chapter_number]
            verse_map: Dict[int, str] = {}
            duplicates: Dict[int, int] = {}

            for verse_data in verses:
                verse_num = verse_data.get('verse')
                if verse_num is None:
                    continue
                verse_text_value = verse_data.get('text', '').strip()
                if verse_num in verse_map:
                    duplicates[verse_num] = duplicates.get(verse_num, 1) + 1
                verse_map[verse_num] = verse_text_value

            chapter = Chapter.objects.create(
                book=book,
                chapter_number=chapter_number,
                total_verses=len(verse_map)
            )
            print(f'Processing chapter {chapter.chapter_number} ({len(verse_map)} unique verses)')
            if duplicates:
                print(f'  Warning: duplicate verse numbers found and merged: {sorted(duplicates.keys())}')

            for verse_num, verse_text_value in sorted(verse_map.items()):
                verse = Verse.objects.create(
                    chapter=chapter,
                    verse_number=verse_num,
                )
                VerseText.objects.create(
                    verse=verse,
                    language=language,
                    text=verse_text_value,
                )
                print(f'  Inserted verse {verse_num}')

        book.total_chapters = book.chapters.count()
        book.save(update_fields=['total_chapters'])

    total_verses = Verse.objects.filter(chapter__book=book).count()
    total_texts = VerseText.objects.filter(verse__chapter__book=book, language=language).count()

    print('\nImport complete:')
    print(f'  Book: {book.name} (id={book.id})')
    print(f'  Language: {language.code}')
    print(f'  Chapters: {book.total_chapters}')
    print(f'  Total Verse rows: {total_verses}')
    print(f'  VerseText rows for {language.code}: {total_texts}')


def import_directory(directory_path: str, language_code: str):
    directory = Path(directory_path)
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f'Directory not found: {directory_path}')

    json_files = sorted(directory.glob('*.json'))
    if not json_files:
        print(f'No JSON files found in {directory_path}')
        return

    for json_file in json_files:
        book_name = format_book_name_from_filename(json_file)
        print('\n' + '=' * 80)
        print(f'Importing {json_file.name} as book "{book_name}"')
        try:
            insert_scraped_book(str(json_file), book_name, language_code)
        except Exception as exc:
            print(f'Failed to import {json_file.name}: {exc}')


if __name__ == '__main__':
    if len(sys.argv) == 3 and Path(sys.argv[1]).is_dir():
        directory = sys.argv[1]
        language_code = sys.argv[2]
        import_directory(directory, language_code)
    elif len(sys.argv) == 4:
        json_file = sys.argv[1]
        book_name = sys.argv[2]
        language_code = sys.argv[3]
        insert_scraped_book(json_file, book_name, language_code)
    else:
        print('Usage:')
        print('  python scripts/insert_scraped_book.py <json-file> <book-name> <language-code>')
        print('  python scripts/insert_scraped_book.py <json-directory> <language-code>')
        print('Example: python scripts/insert_scraped_book.py genesis.json Genesis am')
        print('Example: python scripts/insert_scraped_book.py scripts/am_book am')
        sys.exit(1)
