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
NT_BOOK_NAME_MAP = {
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
}

CLOUDINARY_CONFIG = {
    "cloud_name": "dleykahqd",
    "api_key":    "284571752959753",
    "api_secret": "B-tJyF7f1oBSt9qIulbGNvK8Hbg",
    "secure":     True,
}

DEFAULT_PREFIX = "bible_audio/bibel_audio/new/am/"


class Command(BaseCommand):
    help = "Import New Testament Amharic audio files from Cloudinary into the DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--prefix",
            dest="prefix",
            default=DEFAULT_PREFIX,
            help=f"Cloudinary folder prefix to scan (default: {DEFAULT_PREFIX})",
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

        prefix  = options["prefix"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN — nothing will be written.\n"))

        # ── Fetch all Cloudinary resources under the prefix ─────────────────
        self.stdout.write(f"Scanning Cloudinary prefix: {prefix}")
        all_resources = self._fetch_all_resources(prefix)

        if not all_resources:
            self.stdout.write(self.style.WARNING("No audio files found in Cloudinary."))
            return

        self.stdout.write(f"Found {len(all_resources)} total asset(s).\n")

        # ── Resolve DB fixtures ──────────────────────────────────────────────
        language, _ = Language.objects.get_or_create(
            code="am",
            defaults={"name": "Amharic", "native_name": "አማርኛ"},
        )
        testament, _ = Testament.objects.get_or_create(name="New")

        # ── Process ──────────────────────────────────────────────────────────
        success_count = 0
        skipped_count = 0
        unknown_books  = set()

        def _do_work():
            nonlocal success_count, skipped_count

            for asset in all_resources:
                public_id = asset.get("public_id", "")
                res_type  = asset.get("resource_type", "video")
                parts     = public_id.split("/")

                # Expected path:
                #   bible_audio/bibel_audio/new/am/<book_folder>/<chapter_file>
                # So we need at least 6 parts.
                if len(parts) < 6:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠  Unexpected path (< 6 parts): {public_id}")
                    )
                    skipped_count += 1
                    continue

                raw_folder = parts[4].strip().lower()   # e.g. "1_corinthians"
                filename   = parts[-1]                  # e.g. "3" or "3.mp3"

                # Extract chapter number
                chapter_str = filename.split(".")[0]
                if not chapter_str.isdigit():
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠  Non-numeric filename, skipping: {public_id}")
                    )
                    skipped_count += 1
                    continue

                chapter_num = int(chapter_str)

                # Resolve DB book name
                db_book_name = NT_BOOK_NAME_MAP.get(raw_folder)
                if not db_book_name:
                    unknown_books.add(raw_folder)
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠  No DB mapping for folder '{raw_folder}', skipping."
                        )
                    )
                    skipped_count += 1
                    continue

                # Build direct playback URL
                playback_url = (
                    f"https://res.cloudinary.com/{CLOUDINARY_CONFIG['cloud_name']}"
                    f"/{res_type}/upload/{public_id}"
                )

                self.stdout.write(
                    f"  {'[DRY] ' if dry_run else ''}"
                    f"{db_book_name} ch.{chapter_num}  ←  {public_id}"
                )

                if dry_run:
                    success_count += 1
                    continue

                # ── Book ────────────────────────────────────────────────────
                try:
                    book = Book.objects.get(name__iexact=db_book_name)
                except Book.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"    ✖  Book '{db_book_name}' not found in DB — skipping."
                            f"\n       Run: python manage.py insert_verses --list-books"
                        )
                    )
                    skipped_count += 1
                    continue
                except Book.MultipleObjectsReturned:
                    self.stdout.write(
                        self.style.ERROR(
                            f"    ✖  Multiple books named '{db_book_name}' — skipping."
                        )
                    )
                    skipped_count += 1
                    continue

                # ── Chapter ─────────────────────────────────────────────────
                chapter, _ = Chapter.objects.get_or_create(
                    book=book,
                    chapter_number=chapter_num,
                    defaults={"total_verses": 0},
                )

                # ── ChapterAudio ─────────────────────────────────────────────
                ChapterAudio.objects.update_or_create(
                    book=book,
                    chapter_number=chapter_num,
                    language=language,
                    defaults={
                        "chapter":              chapter,
                        "audio_url":            playback_url,
                        "cloudinary_public_id": public_id,
                        "is_available":         True,
                    },
                )

                success_count += 1

            if not dry_run:
                self._sync_book_meta(testament, language)

        if dry_run:
            _do_work()
        else:
            with transaction.atomic():
                _do_work()

        # ── Summary ──────────────────────────────────────────────────────────
        self.stdout.write("")
        if unknown_books:
            self.stdout.write(
                self.style.WARNING(
                    "Cloudinary folders with no NT_BOOK_NAME_MAP entry:\n"
                    + "\n".join(f"  • {f}" for f in sorted(unknown_books))
                    + "\nAdd them to NT_BOOK_NAME_MAP in this command file."
                )
            )

        style = self.style.SUCCESS if not dry_run else self.style.WARNING
        prefix_label = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            style(
                f"\n{prefix_label}Done!"
                f"\n  Processed : {success_count}"
                f"\n  Skipped   : {skipped_count}"
            )
        )

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