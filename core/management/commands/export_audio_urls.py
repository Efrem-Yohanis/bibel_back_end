"""
Django management command: insert_en_audio_json
Reads bible_en_audio.json and inserts all URLs into ChapterAudio for English.
Place at:
    core/management/commands/insert_en_audio_json.py
Usage:
    python manage.py insert_en_audio_json
    python manage.py insert_en_audio_json --dry-run
"""

import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Book, Chapter, ChapterAudio, Language, Testament


JSON_FILE = Path.home() / "english_audio" / "bible_en_audio.json"
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
    help = "Insert English Bible audio URLs from bible_en_audio.json into the DB."
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--json", default=None, help="Custom path to JSON file")

    def handle(self, *args, **options):
        dry_run  = options["dry_run"]
        json_path = Path(options["json"]) if options["json"] else JSON_FILE

        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {json_path}"))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN — nothing will be written.\n"))

        data = json.loads(json_path.read_text(encoding="utf-8"))

        # Flatten both testaments into one dict: book_name → {chapter: url}
        all_books: dict[str, dict[str, str]] = {}
        for section in data.values():          # old_testament, new_testament
            all_books.update(section)

        self.stdout.write(f"Found {len(all_books)} books in JSON.\n")

        # Get or create fixtures
        language, _  = Language.objects.get_or_create(code="en", defaults={"name": "English"})
        ot, _        = Testament.objects.get_or_create(name="Old")
        nt, _        = Testament.objects.get_or_create(name="New")

        ok = fail = created_books = 0

        with transaction.atomic():
            for book_name, chapters in all_books.items():

                testament = ot if book_name in OT_BOOKS else nt

                # Get or create Book
                book, book_created = Book.objects.get_or_create(
                    name__iexact=book_name,
                    defaults={
                        "name": book_name,
                        "testament": testament,
                        "has_audio": True,
                        "bible_order": 0,
                    }
                )
                if book_created:
                    created_books += 1
                    self.stdout.write(f"  📖 Created book: {book_name}")

                self.stdout.write(f"\n{book_name} ({len(chapters)} chapters)")

                for chapter_str, audio_url in sorted(chapters.items(), key=lambda x: int(x[0])):
                    chapter_num = int(chapter_str)

                    if dry_run:
                        self.stdout.write(f"  [DRY] Ch {chapter_num:>3}  {audio_url}")
                        ok += 1
                        continue

                    try:
                        # Extract public_id from URL  e.g. .../upload/v123/bible_audio/.../1.mp3
                        public_id = audio_url.split("/upload/")[-1]
                        # Strip version prefix like v1780766512/
                        if public_id.startswith("v") and "/" in public_id:
                            public_id = public_id.split("/", 1)[1]

                        chapter_obj, _ = Chapter.objects.get_or_create(
                            book=book,
                            chapter_number=chapter_num,
                            defaults={"total_verses": 0},
                        )

                        ChapterAudio.objects.update_or_create(
                            book=book,
                            chapter_number=chapter_num,
                            language=language,
                            defaults={
                                "chapter": chapter_obj,
                                "audio_url": audio_url,
                                "cloudinary_public_id": public_id,
                                "is_available": True,
                            },
                        )
                        self.stdout.write(f"  ✓ Ch {chapter_num:>3}  {audio_url}")
                        ok += 1

                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  ✗ Ch {chapter_num}: {e}"))
                        fail += 1

                # Update book metadata
                if not dry_run:
                    book.total_chapters = Chapter.objects.filter(book=book).count()
                    book.has_audio = True
                    book.save(update_fields=["total_chapters", "has_audio"])

        self.stdout.write(self.style.SUCCESS(
            f"\n{'='*50}\n"
            f"Done!\n"
            f"  Books created : {created_books}\n"
            f"  Chapters done : {ok}\n"
            f"  Failed        : {fail}"
        ))