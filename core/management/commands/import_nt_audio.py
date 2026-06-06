"""
Django management command: import_nt_audio

Place this file at:
    core/management/commands/import_nt_audio.py

Usage
-----
python manage.py import_nt_audio
python manage.py import_nt_audio --dry-run
python manage.py import_nt_audio --prefix bible_audio/bibel_audio/new/am/
"""

import os
import re
import cloudinary
from cloudinary import api
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Book, Chapter, ChapterAudio, Language, Testament


# ---------------------------------------------------------------------------
# Filename stem → exact DB book name (Amharic)
# Keys must match the Cloudinary folder name (lower-cased).
# Run --list-books to verify names against your DB.
# ---------------------------------------------------------------------------
BOOK_NAME_MAP = {
    "matthew":          "ማቴዎስ",
    "mark":             "ማርቆስ",
    "luke":             "ሉቃስ",
    "john":             "ዮሐንስ",
    "acts":             "የሐዋርያት ሥራ",
    "romans":           "ሮሜ",
    "1_corinthians":    "1ኛ ቆሮንቶስ",
    "2_corinthians":    "2ኛ ቆሮንቶስ",
    "galatians":        "ገላትያ",
    "ephesians":        "ኤፌሶን",
    "philippians":      "ፊልጵስዩስ",
    "colossians":       "ቆላስይስ",
    "1_thessalonians":  "1ኛ ተሰሎንቄ",
    "2_thessalonians":  "2ኛ ተሰሎንቄ",
    "1_timothy":        "1ኛ ጢሞቴዎስ",
    "2_timothy":        "2ኛ ጢሞቴዎስ",
    "titus":            "ቲቶ",
    "philemon":         "ፊልሞና",
    "hebrews":          "ዕብራውያን",
    "james":            "ያዕቆብ",
    "1_peter":          "1ኛ ጴጥሮስ",
    "2_peter":          "2ኛ ጴጥሮስ",
    "1_john":           "1ኛ ዮሐንስ",
    "2_john":           "2ኛ ዮሐንስ",
    "3_john":           "3ኛ ዮሐንስ",
    "jude":             "ይሁዳ",
    "revelation":       "ራዕይ",
    "acts_part1":       "የሐዋርያት ሥራ",
    "acts_part2":       "የሐዋርያት ሥራ",
    "john_part1":       "ዮሐንስ",
    "john_part2":       "ዮሐንስ",
    "luke_part1":       "ሉቃስ",
    "luke_part2":       "ሉቃስ",
    "mark_part1":       "ማርቆስ",
    "mark_part2":       "ማርቆስ",
    "matthew_part1":    "ማቴዎስ",
    "matthew_part2":    "ማቴዎስ",
    "genesis":          "ዘፍጥረት",
    "exodus":           "ዘጸአት",
    "leviticus":        "ዘሌዋውያን",
    "numbers":          "ዘቍጥር",
    "deuteronomy":       "ዘዳግም",
    "joshua":           "ኢያሱ",
    "judges":           "መሳፍንት",
    "ruth":             "ሩት",
    "1_samuel":         "1ኛ ሳሙኤል",
    "2_samuel":         "2ኛ ሳሙኤል",
    "1_kings":          "1ኛ ነገሥት",
    "2_kings":          "2ኛ ነገሥት",
    "1_chronicles":     "1ኛ ዜና መዋዕል",
    "2_chronicles":     "2ኛ ዜና መዋዕል",
    "ezra":             "ዕዝራ",
    "nehemiah":         "ነህምያ",
    "esther":           "አስቴር",
    "job":              "ኢዮብ",
    "psalms":           "መዝሙር",
    "psalm":            "መዝሙር",
    "psalms_part_1":    "መዝሙር",
    "psalms_part_2":    "መዝሙር",
    "psalms_part_3":    "መዝሙር",
    "proverbs":         "ምሳሌ",
    "ecclesiastes":     "መክብብ",
    "song_of_solomon":  "መኃልየ መኃልይ ዘሰሎሞን",
    "isaiah":           "ኢሳይያስ",
    "jeremiah":         "ኤርምያስ",
    "lamentations":     "ሰቆቃወ ኤርምያስ",
    "ezekiel":          "ሕዝቅኤል",
    "daniel":           "ዳንኤል",
    "hosea":            "ሆሴዕ",
    "joel":             "ኢዩኤል",
    "amos":             "አሞጽ",
    "obadiah":          "አብድዩ",
    "jonah":            "ዮናስ",
    "micah":            "ሚክያስ",
    "nahum":            "ናሆም",
    "habakkuk":         "ዕንባቆም",
    "zephaniah":        "ሶፎንያስ",
    "haggai":           "ሐጌ",
    "zechariah":        "ዘካርያስ",
    "malachi":          "ሚልክያስ",
}

# For English we can derive book names by formatting the folder name.
# For Amharic we rely on the explicit map above.

def _derive_english_book_name(folder_name: str) -> str:
    # Convert underscores to spaces and title case. Handles '1_chronicles' -> '1 Chronicles'
    name = folder_name.replace("_", " ").strip()
    # Ensure numeric prefixes stay as numbers followed by capitalized word
    # Title-case the rest
    return name.title()


def _normalize_cloudinary_folder_name(folder_name: str) -> str:
    folder = folder_name.strip().lower()
    folder = folder.replace(" ", "_")
    folder = folder.replace("-", "_")
    folder = re.sub(r"__+", "_", folder)
    folder = folder.strip("_")
    return folder


def _resolve_db_book_name(raw_folder: str, language_code: str) -> str:
    normalized_folder = _normalize_cloudinary_folder_name(raw_folder)
    db_book_name = BOOK_NAME_MAP.get(normalized_folder)
    if db_book_name:
        return db_book_name

    # Try removing part suffixes like _part1/_part2/_part_1
    canonical = re.sub(r"_part(?:_)?\d+$", "", normalized_folder)
    if canonical != normalized_folder:
        db_book_name = BOOK_NAME_MAP.get(canonical)
        if db_book_name:
            return db_book_name

    # Some Cloudinary folders use 'song_of_songs'
    if normalized_folder == "song_of_songs":
        return BOOK_NAME_MAP.get("song_of_solomon")

    # Do not guess book names for English audio; explicit mapping is required.
    return None

# Cloudinary config uses environment variables when available (safer for production)
CLOUDINARY_CONFIG = {
    "cloud_name": os.environ.get("CLOUDINARY_NAME", "dleykahqd"),
    "api_key":    os.environ.get("CLOUDINARY_API_KEY", "284571752959753"),
    "api_secret": os.environ.get("CLOUDINARY_API_SECRET", "B-tJyF7f1oBSt9qIulbGNvK8Hbg"),
    "secure":     True,
}

DEFAULT_PREFIX = "bible_audio/bibel_audio/new/am/"
DEFAULT_PREFIXES = {
    'new': lambda lang: f"bible_audio/bibel_audio/new/{lang}/",
    'old': lambda lang: f"bible_audio/bibel_audio/old/{lang}/",
}


class Command(BaseCommand):
    help = "Import Cloudinary audio files into the DB (supports language & testament selection)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--prefix",
            dest="prefix",
            default=None,
            help=f"Cloudinary folder prefix to scan (default: built from --testament and --language)",
        )
        parser.add_argument(
            "--language",
            dest="language",
            default=None,
            help="Language code to import (en, am, or, ti). If omitted, the prefix language will be inferred.",
        )
        parser.add_argument(
            "--testament",
            dest="testament",
            default="new",
            choices=["new", "old", "both"],
            help="Which testament folders to scan: new, old, or both",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Fetch metadata and show what would be imported without writing to DB.",
        )
        parser.add_argument(
            "--list-books",
            action="store_true",
            dest="list_books",
            help="Print all NT books currently in the DB and exit.",
        )

    # ------------------------------------------------------------------ handle

    def handle(self, *args, **options):
        if options["list_books"]:
            self._list_books()
            return

        cloudinary.config(**CLOUDINARY_CONFIG)

        prefix  = options.get("prefix")
        dry_run = options.get("dry_run")
        language_code = options.get("language")
        testament_choice = options.get("testament", "new")

        if not language_code and prefix:
            match = re.search(r"/bibel_audio/(?:new|old)/([a-z]{2})/", prefix.lower())
            if match:
                language_code = match.group(1)
                self.stdout.write(self.style.WARNING(f"Inferring language from prefix: {language_code}"))

        if not language_code:
            language_code = "am"

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN — nothing will be written.\n"))

        # ── Fetch all Cloudinary resources under the prefix ─────────────────
        # Determine prefixes to scan
        prefixes = []
        if prefix:
            prefixes = [prefix]
        else:
            if testament_choice in ("new", "both"):
                prefixes.append(DEFAULT_PREFIXES['new'](language_code))
            if testament_choice in ("old", "both"):
                prefixes.append(DEFAULT_PREFIXES['old'](language_code))

        total_assets = 0
        all_resources = []
        for p in prefixes:
            self.stdout.write(f"Scanning Cloudinary prefix: {p}")
            batch = self._fetch_all_resources(p)
            self.stdout.write(f"  Found {len(batch)} assets under {p}.")
            total_assets += len(batch)
            # tag resources with prefix so we can diagnose unknown folders per prefix
            for r in batch:
                r['_scanned_prefix'] = p
            all_resources.extend(batch)

        if not all_resources:
            self.stdout.write(self.style.WARNING("No audio files found in Cloudinary."))
            return

        self.stdout.write(f"Found {total_assets} total asset(s).\n")

        # Resolve DB fixtures
        language, _ = Language.objects.get_or_create(
            code=language_code,
            defaults={"name": "Amharic" if language_code == 'am' else 'English', "native_name": "አማርኛ" if language_code == 'am' else None},
        )

        success_count = 0
        skipped_count = 0
        unknown_books = set()

        def _do_work(resources):
            nonlocal success_count, skipped_count

            for asset in resources:
                public_id = asset.get("public_id", "")
                res_type = asset.get("resource_type", "video")
                parts = public_id.split("/")

                # Expect at least: bible_audio/bibel_audio/{testament}/{lang}/{book_folder}/{file}
                if len(parts) < 6:
                    self.stdout.write(self.style.WARNING(f"  ⚠  Unexpected path (< 6 parts): {public_id}"))
                    skipped_count += 1
                    continue

                raw_folder = parts[4].strip().lower()
                filename = parts[-1]

                chapter_str = filename.split(".")[0]
                if not chapter_str.isdigit():
                    self.stdout.write(self.style.WARNING(f"  ⚠  Non-numeric filename, skipping: {public_id}"))
                    skipped_count += 1
                    continue

                chapter_num = int(chapter_str)

                # Resolve DB book name from known Cloudinary folder mapping.
                db_book_name = _resolve_db_book_name(raw_folder, language_code)

                if not db_book_name:
                    unknown_books.add(raw_folder)
                    self.stdout.write(self.style.WARNING(f"  ⚠  No DB mapping for folder '{raw_folder}', skipping."))
                    skipped_count += 1
                    continue

                playback_url = f"https://res.cloudinary.com/{CLOUDINARY_CONFIG['cloud_name']}/{res_type}/upload/{public_id}"

                self.stdout.write(f"  {'[DRY] ' if dry_run else ''}{db_book_name} ch.{chapter_num}  ←  {public_id}")

                if dry_run:
                    success_count += 1
                    continue

                # Book
                try:
                    book = Book.objects.get(name__iexact=db_book_name)
                except Book.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"    ✖  Book '{db_book_name}' not found in DB — skipping.\n       Run: python manage.py insert_verses --list-books"))
                    skipped_count += 1
                    continue
                except Book.MultipleObjectsReturned:
                    self.stdout.write(self.style.ERROR(f"    ✖  Multiple books named '{db_book_name}' — skipping."))
                    skipped_count += 1
                    continue

                # Chapter
                chapter, _ = Chapter.objects.get_or_create(book=book, chapter_number=chapter_num, defaults={"total_verses": 0})

                # ChapterAudio
                ChapterAudio.objects.update_or_create(
                    book=book,
                    chapter_number=chapter_num,
                    language=language,
                    defaults={
                        "chapter": chapter,
                        "audio_url": playback_url,
                        "cloudinary_public_id": public_id,
                        "is_available": True,
                    },
                )

                success_count += 1

        # Run work either in transaction or dry-run
        if dry_run:
            _do_work(all_resources)
        else:
            with transaction.atomic():
                _do_work(all_resources)

        # Sync metadata per testament selection
        if testament_choice in ('new', 'both'):
            nt_testament, _ = Testament.objects.get_or_create(name="New")
            self._sync_book_meta(nt_testament, language)
        if testament_choice in ('old', 'both'):
            ot_testament, _ = Testament.objects.get_or_create(name="Old")
            self._sync_book_meta(ot_testament, language)

        # Summary
        self.stdout.write("")
        if unknown_books:
            self.stdout.write(self.style.WARNING("Cloudinary folders with no mapping:\n" + "\n".join(f"  • {f}" for f in sorted(unknown_books)) + "\n"))

        style = self.style.SUCCESS if not dry_run else self.style.WARNING
        prefix_label = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(style(f"\n{prefix_label}Done!\n  Processed : {success_count}\n  Skipped   : {skipped_count}"))

    # -------------------------------------------------------- helpers

    def _fetch_all_resources(self, prefix: str):
        """Paginate through Cloudinary API to collect every asset under prefix."""
        all_resources = []
        next_cursor   = None

        while True:
            kwargs = {
                "type":          "upload",
                "resource_type": "video",
                "prefix":        prefix,
                "max_results":   500,
            }
            if next_cursor:
                kwargs["next_cursor"] = next_cursor

            response     = api.resources(**kwargs)
            batch        = response.get("resources", [])
            all_resources.extend(batch)

            self.stdout.write(
                f"  Fetched {len(batch)} assets (total so far: {len(all_resources)})"
            )

            next_cursor = response.get("next_cursor")
            if not next_cursor:
                break

        return all_resources

    def _sync_book_meta(self, testament, language):
        """Update total_chapters and has_audio on every NT Book."""
        self.stdout.write("\nSyncing book metadata...")
        nt_books = Book.objects.filter(testament=testament)
        for book in nt_books:
            chapter_count = Chapter.objects.filter(book=book).count()
            audio_count   = ChapterAudio.objects.filter(
                book=book, language=language, is_available=True
            ).count()

            changed = False
            if chapter_count > 0 and book.total_chapters != chapter_count:
                book.total_chapters = chapter_count
                changed = True
            if audio_count > 0 and not book.has_audio:
                book.has_audio = True
                changed = True
            if changed:
                book.save(update_fields=["total_chapters", "has_audio"])
                self.stdout.write(
                    f"  Updated {book.name}: "
                    f"chapters={chapter_count}, has_audio={book.has_audio}"
                )

    def _list_books(self):
        nt = Testament.objects.filter(name="New").first()
        if not nt:
            self.stdout.write(self.style.ERROR("No 'New' testament found in DB."))
            return
        books = Book.objects.filter(testament=nt).order_by("bible_order")
        self.stdout.write(
            self.style.HTTP_INFO(f"{'pk':>6}  {'order':>5}  name")
        )
        self.stdout.write("─" * 50)
        for b in books:
            self.stdout.write(f"{b.pk:>6}  {b.bible_order:>5}  {b.name}")
        self.stdout.write(f"\nTotal: {books.count()} NT books")