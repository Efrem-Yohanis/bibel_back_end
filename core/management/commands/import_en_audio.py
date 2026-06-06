"""
Django management command: import_en_audio

Reads the JSON url maps produced by split_and_upload.py and inserts
ChapterAudio records for English (lang code: en).

Place at:
    core/management/commands/import_en_audio.py

Usage:
    python manage.py import_en_audio
    python manage.py import_en_audio --dry-run
    python manage.py import_en_audio --book Genesis
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Book, Chapter, ChapterAudio, Language, Testament


# Path to the JSON files saved by split_and_upload.py
URL_MAPS_DIR = Path.home() / "english_audio" / "url_maps"

# Which testament each book belongs to
OT_BOOKS = {
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi",
}


class Command(BaseCommand):
    help = "Import English Bible audio URLs from JSON maps into ChapterAudio."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be inserted without writing to DB.",
        )
        parser.add_argument(
            "--book",
            dest="book",
            default=None,
            help="Import only one book by name, e.g. --book Genesis",
        )

    def handle(self, *args, **options):
        dry_run  = options["dry_run"]
        only_book = options["book"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN — nothing will be written.\n"))

        if not URL_MAPS_DIR.exists():
            self.stdout.write(self.style.ERROR(f"url_maps folder not found: {URL_MAPS_DIR}"))
            return

        # Get or create English language
        language, _ = Language.objects.get_or_create(
            code="en",
            defaults={"name": "English"},
        )

        ot_testament, _ = Testament.objects.get_or_create(name="Old")
        nt_testament, _ = Testament.objects.get_or_create(name="New")

        # Collect JSON files to process
        if only_book:
            json_files = [URL_MAPS_DIR / f"{only_book}.json"]
        else:
            json_files = sorted(URL_MAPS_DIR.glob("*.json"))
            json_files = [f for f in json_files if not f.name.startswith("_")]

        if not json_files:
            self.stdout.write(self.style.ERROR("No JSON files found in url_maps/"))
            return

        total_ok = total_skip = total_fail = 0

        with transaction.atomic():
            for json_file in json_files:
                if not json_file.exists():
                    self.stdout.write(self.style.ERROR(f"File not found: {json_file}"))
                    continue

                book_name = json_file.stem   # e.g. "Genesis"
                urls: dict = json.loads(json_file.read_text(encoding="utf-8"))

                self.stdout.write(f"\n📖 {book_name} ({len(urls)} chapters)")

                # Look up the Book in DB
                try:
                    book = Book.objects.get(name__iexact=book_name)
                except Book.DoesNotExist:
                    # Try to create it if missing
                    testament = ot_testament if book_name in OT_BOOKS else nt_testament
                    if not dry_run:
                        book = Book.objects.create(
                            name=book_name,
                            testament=testament,
                            has_audio=True,
                            bible_order=0,
                        )
                        self.stdout.write(self.style.WARNING(f"  Created missing book: {book_name}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  [DRY] Would create book: {book_name}"))
                        total_skip += len(urls)
                        continue
                except Book.MultipleObjectsReturned:
                    self.stdout.write(self.style.ERROR(f"  Multiple DB rows for '{book_name}', skipping."))
                    total_skip += len(urls)
                    continue

                ok = fail = 0
                for chapter_str, audio_url in sorted(urls.items(), key=lambda x: int(x[0])):
                    chapter_num = int(chapter_str)

                    self.stdout.write(
                        f"  {'[DRY] ' if dry_run else ''}Ch {chapter_num:>3}  {audio_url}"
                    )

                    if dry_run:
                        ok += 1
                        continue

                    try:
                        # Get or create Chapter
                        chapter, _ = Chapter.objects.get_or_create(
                            book=book,
                            chapter_number=chapter_num,
                            defaults={"total_verses": 0},
                        )

                        # Upsert ChapterAudio
                        ChapterAudio.objects.update_or_create(
                            book=book,
                            chapter_number=chapter_num,
                            language=language,
                            defaults={
                                "chapter": chapter,
                                "audio_url": audio_url,
                                "cloudinary_public_id": audio_url.split("/upload/")[-1],
                                "is_available": True,
                            },
                        )
                        ok += 1

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"    ✗ Ch {chapter_num}: {e}"))
                        fail += 1

                # Update book metadata
                if not dry_run:
                    chapter_count = Chapter.objects.filter(book=book).count()
                    book.total_chapters = chapter_count
                    book.has_audio = True
                    book.save(update_fields=["total_chapters", "has_audio"])

                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ {ok} inserted") +
                    (self.style.ERROR(f"  ✗ {fail} failed") if fail else "")
                )
                total_ok   += ok
                total_fail += fail

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(self.style.SUCCESS(
            f"Done!\n"
            f"  Inserted : {total_ok}\n"
            f"  Skipped  : {total_skip}\n"
            f"  Failed   : {total_fail}"
        ))