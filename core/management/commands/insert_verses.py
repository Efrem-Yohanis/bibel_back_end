"""
Django management command: insert_verses

Place this file at:
    core/management/commands/insert_verses.py

Make sure these __init__.py files exist (can be empty):
    core/management/__init__.py
    core/management/commands/__init__.py

Usage
-----
# List all books in DB to find exact names
python manage.py insert_verses --list-books

# Single file
python manage.py insert_verses path/to/1_corinthians.json --book "1ኛ ቆሮንቶስ" --lang am

# Entire directory (uses built-in filename → DB name map)
python manage.py insert_verses path/to/nt_books/ --lang am

# Dry-run (no DB writes, just shows counts)
python manage.py insert_verses path/to/nt_books/ --lang am --dry-run

# Insert only, never overwrite existing VerseText rows
python manage.py insert_verses path/to/nt_books/ --lang am --no-overwrite

# Use a custom JSON map file  {"stem": "DB name", ...}
python manage.py insert_verses path/to/nt_books/ --lang am --map path/to/mymap.json
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Book, Chapter, Language, Verse, VerseText


# ---------------------------------------------------------------------------
# Filename stem (lower-case) → Amharic DB book name
# Covers both bare names and numbered prefixes.
# Add/edit entries here whenever you add new source files.
# ---------------------------------------------------------------------------
DEFAULT_NAME_MAP: Dict[str, str] = {
    # ── New Testament ────────────────────────────────────────────────────────
    "matthew":              "ማቴዎስ",
    "1_matthew":            "ማቴዎስ",
    "mark":                 "ማርቆስ",
    "2_mark":               "ማርቆስ",
    "luke":                 "ሉቃስ",
    "3_luke":               "ሉቃስ",
    "john":                 "ዮሐንስ",
    "4_john":               "ዮሐንስ",
    "acts":                 "የሐዋርያት ሥራ",
    "5_acts":               "የሐዋርያት ሥራ",
    "romans":               "ሮሜ",
    "6_romans":             "ሮሜ",
    "1_corinthians":        "1ኛ ቆሮንቶስ",
    "7_1_corinthians":      "1ኛ ቆሮንቶስ",
    "2_corinthians":        "2ኛ ቆሮንቶስ",
    "8_2_corinthians":      "2ኛ ቆሮንቶስ",
    "galatians":            "ገላትያ",
    "9_galatians":          "ገላትያ",
    "ephesians":            "ኤፌሶን",
    "10_ephesians":         "ኤፌሶን",
    "philippians":          "ፊልጵስዩስ",
    "11_philippians":       "ፊልጵስዩስ",
    "colossians":           "ቆላስይስ",
    "12_colossians":        "ቆላስይስ",
    "1_thessalonians":      "1ኛ ተሰሎንቄ",
    "13_1_thessalonians":   "1ኛ ተሰሎንቄ",
    "2_thessalonians":      "2ኛ ተሰሎንቄ",
    "14_2_thessalonians":   "2ኛ ተሰሎንቄ",
    "1_timothy":            "1ኛ ጢሞቴዎስ",
    "15_1_timothy":         "1ኛ ጢሞቴዎስ",
    "2_timothy":            "2ኛ ጢሞቴዎስ",
    "16_2_timothy":         "2ኛ ጢሞቴዎስ",
    "titus":                "ቲቶ",
    "17_titus":             "ቲቶ",
    "philemon":             "ፊልሞና",
    "18_philemon":          "ፊልሞና",
    "hebrews":              "ዕብራውያን",
    "19_hebrews":           "ዕብራውያን",
    "james":                "ያዕቆብ",
    "20_james":             "ያዕቆብ",
    "1_peter":              "1ኛ ጴጥሮስ",
    "21_1_peter":           "1ኛ ጴጥሮስ",
    "2_peter":              "2ኛ ጴጥሮስ",
    "22_2_peter":           "2ኛ ጴጥሮስ",
    "1_john":               "1ኛ ዮሐንስ",
    "23_1_john":            "1ኛ ዮሐንስ",
    "2_john":               "2ኛ ዮሐንስ",
    "24_2_john":            "2ኛ ዮሐንስ",
    "3_john":               "3ኛ ዮሐንስ",
    "25_3_john":            "3ኛ ዮሐንስ",
    "jude":                 "ይሁዳ",
    "26_jude":              "ይሁዳ",
    # ⚠ Revelation: update the value below after running --list-books
    "revelation":           "ራእይ ዮሐንስ",
    "27_revelation":        "ራእይ ዮሐንስ",

    # ── Old Testament ────────────────────────────────────────────────────────
    "genesis":              "ዘፍጥረት",
    "exodus":               "ዘጸአት",
    "leviticus":            "ዘሌዋውያን",
    "numbers":              "ዘቍጥር",
    "deuteronomy":          "ዘዳግም",
    "joshua":               "ኢያሱ",
    "judges":               "መሳፍንት",
    "ruth":                 "ሩት",
    "1_samuel":             "1ኛ ሳሙኤል",
    "2_samuel":             "2ኛ ሳሙኤል",
    "1_kings":              "1ኛ ነገሥት",
    "2_kings":              "2ኛ ነገሥት",
    "1_chronicles":         "1ኛ ዜና መዋዕል",
    "2_chronicles":         "2ኛ ዜና መዋዕል",
    "ezra":                 "ዕዝራ",
    "nehemiah":             "ነህምያ",
    "esther":               "አስቴር",
    "job":                  "ኢዮብ",
    "psalms":               "መዝሙር",
    "psalm":                "መዝሙር",
    "proverbs":             "ምሳሌ",
    "ecclesiastes":         "መክብብ",
    "song_of_solomon":      "መኃልየ መኃልይ ዘሰሎሞን",
    "isaiah":               "ኢሳይያስ",
    "jeremiah":             "ኤርምያስ",
    "lamentations":         "ሰቆቃወ ኤርምያስ",
    "ezekiel":              "ሕዝቅኤል",
    "daniel":               "ዳንኤል",
    "hosea":                "ሆሴዕ",
    "joel":                 "ኢዩኤል",
    "amos":                 "አሞጽ",
    "obadiah":              "አብድዩ",
    "jonah":                "ዮናስ",
    "micah":                "ሚክያስ",
    "nahum":                "ናሆም",
    "habakkuk":             "ዕንባቆም",
    "zephaniah":            "ሶፎንያስ",
    "haggai":               "ሐጌ",
    "zechariah":            "ዘካርያስ",
    "malachi":              "ሚልክያስ",
}


# ---------------------------------------------------------------------------
# JSON / parsing helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Dict[str, Any]:
    encodings = ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError:
            continue
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {path.name}: {exc}")
    raise CommandError(f"Cannot decode {path.name} with any supported encoding.")


def _parse_chapter_number(title: str) -> int:
    if not title:
        return 1
    m = re.search(r"(?:ምዕራፍ|chapter)\s*(\d+)", title, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"^(\d+)$", title.strip())
    if m:
        return int(m.group(1))
    return 1


def _normalize_chapters(data: Dict[str, Any]) -> Dict[int, List[Dict[str, Any]]]:
    """Return {chapter_number: [verse_dict, ...]}"""
    if "chapters" in data:
        chapters = data["chapters"]

        if isinstance(chapters, dict):
            result: Dict[int, List] = {}
            for k, v in chapters.items():
                try:
                    num = int(k)
                except (TypeError, ValueError):
                    continue
                result[num] = v.get("verses", []) if isinstance(v, dict) else []
            return result

        if isinstance(chapters, list):
            result = {}
            for item in chapters:
                if not isinstance(item, dict):
                    continue
                num = item.get("chapter")
                if num is None:
                    num = _parse_chapter_number(item.get("title", ""))
                try:
                    num = int(num)
                except (TypeError, ValueError):
                    continue
                verses = item.get("verses", [])
                if isinstance(verses, list):
                    result[num] = verses
            return result

    if "verses" in data and isinstance(data["verses"], list):
        num = _parse_chapter_number(data.get("chapter_title", ""))
        return {num: data["verses"]}

    raise CommandError(
        "Unsupported JSON format — expected 'chapters' or 'verses' at root."
    )


# ---------------------------------------------------------------------------
# Management command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = (
        "Insert/update verse texts from JSON file(s) into EXISTING Book records. "
        "The Book row itself (testament, bible_order, etc.) is never touched."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            nargs="?",
            metavar="FILE_OR_DIR",
            help="Path to a JSON file or a directory containing JSON files.",
        )
        parser.add_argument(
            "--book", "-b",
            dest="book_name",
            metavar="NAME",
            help=(
                "DB book name (case-insensitive). "
                "Required when source is a single file."
            ),
        )
        parser.add_argument(
            "--lang", "-l",
            dest="language_code",
            default="am",
            metavar="CODE",
            help="Language code to insert/update (default: am).",
        )
        parser.add_argument(
            "--map", "-m",
            dest="map_file",
            metavar="JSON_FILE",
            help=(
                'Path to a JSON file mapping filename stems to DB book names. '
                'Format: {"stem": "DB name", ...}. '
                "Merged on top of the built-in map."
            ),
        )
        parser.add_argument(
            "--no-overwrite",
            action="store_true",
            dest="no_overwrite",
            help="Skip updating VerseText rows that already exist.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Show what would be done without writing anything to the DB.",
        )
        parser.add_argument(
            "--list-books",
            action="store_true",
            dest="list_books",
            help="Print every Book in the DB (pk, order, testament, name) and exit.",
        )

    # ------------------------------------------------------------------ handle

    def handle(self, *args, **options):
        if options["list_books"]:
            self._list_books()
            return

        source = options.get("source")
        if not source:
            raise CommandError(
                "Provide a source path (file or directory), or use --list-books."
            )

        source_path = Path(source)
        lang_code   = options["language_code"]
        overwrite   = not options["no_overwrite"]
        dry_run     = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING("DRY-RUN — nothing will be written to the DB.\n")
            )

        # Build name map (built-in + optional override file)
        name_map = dict(DEFAULT_NAME_MAP)
        if options.get("map_file"):
            map_path = Path(options["map_file"])
            if not map_path.is_file():
                raise CommandError(f"Map file not found: {map_path}")
            try:
                extra: Dict[str, str] = json.loads(
                    map_path.read_text(encoding="utf-8")
                )
                name_map.update({k.lower(): v for k, v in extra.items()})
                self.stdout.write(
                    f"Loaded {len(extra)} extra entries from {map_path.name}.\n"
                )
            except json.JSONDecodeError as exc:
                raise CommandError(f"Invalid JSON in map file: {exc}")

        if source_path.is_dir():
            self._import_directory(source_path, lang_code, name_map, overwrite, dry_run)
        elif source_path.is_file():
            book_name = options.get("book_name")
            if not book_name:
                raise CommandError(
                    "--book <DB book name> is required when the source is a single file.\n"
                    "Run: python manage.py insert_verses --list-books"
                )
            self._import_file(source_path, book_name, lang_code, overwrite, dry_run)
        else:
            raise CommandError(f"Source not found: {source_path}")

    # ----------------------------------------------------------- list books

    def _list_books(self):
        books = Book.objects.select_related("testament").order_by("bible_order", "id")
        self.stdout.write(
            self.style.HTTP_INFO(f"{'pk':>6}  {'order':>5}  {'testament':<20}  name")
        )
        self.stdout.write("─" * 70)
        for b in books:
            testament = b.testament.name if b.testament else "—"
            self.stdout.write(
                f"{b.pk:>6}  {b.bible_order:>5}  {testament:<20}  {b.name}"
            )
        self.stdout.write(f"\nTotal: {books.count()} books")

    # ------------------------------------------------------- directory mode

    def _import_directory(
        self,
        directory: Path,
        lang_code: str,
        name_map: Dict[str, str],
        overwrite: bool,
        dry_run: bool,
    ):
        json_files = sorted(directory.glob("*.json"))
        if not json_files:
            raise CommandError(f"No JSON files found in {directory}")

        self.stdout.write(f"Found {len(json_files)} JSON file(s) in {directory}\n")

        skipped_files = []
        for json_file in json_files:
            stem    = json_file.stem.lower()
            db_name = name_map.get(stem)

            self.stdout.write("═" * 70)
            if db_name:
                self.stdout.write(f"File : {json_file.name}")
                self.stdout.write(f'Book : "{db_name}"')
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"File : {json_file.name}\n"
                        f'  ⚠  Stem "{stem}" not in name map — skipped.\n'
                        f"  Tip: add it via --map or update DEFAULT_NAME_MAP."
                    )
                )
                skipped_files.append(json_file.name)
                continue

            try:
                self._import_file(json_file, db_name, lang_code, overwrite, dry_run)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"  ✖  FAILED: {exc}"))

        if skipped_files:
            self.stdout.write(
                self.style.WARNING(
                    f"\n{len(skipped_files)} file(s) skipped (not in name map):\n"
                    + "\n".join(f"  • {f}" for f in skipped_files)
                )
            )

    # ------------------------------------------------------------ file mode

    def _import_file(
        self,
        json_path: Path,
        book_name: str,
        lang_code: str,
        overwrite: bool,
        dry_run: bool,
    ):
        data          = _load_json(json_path)
        chapters_data = _normalize_chapters(data)

        # ── Language ────────────────────────────────────────────────────────
        language, lang_created = Language.objects.get_or_create(
            code=lang_code,
            defaults={"name": lang_code, "native_name": lang_code},
        )
        if lang_created:
            self.stdout.write(f"  Created language: {lang_code}")

        # ── Book ─────────────────────────────────────────────────────────────
        try:
            book = Book.objects.get(name__iexact=book_name)
        except Book.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    f'  ✖  Book "{book_name}" not found in DB.\n'
                    f"     Run: python manage.py insert_verses --list-books"
                )
            )
            return
        except Book.MultipleObjectsReturned:
            dupes = Book.objects.filter(name__iexact=book_name)
            self.stdout.write(
                self.style.ERROR(
                    f'  ✖  Multiple books named "{book_name}": '
                    + ", ".join(f"pk={b.pk}" for b in dupes)
                    + ". Resolve duplicates first."
                )
            )
            return

        self.stdout.write(
            f"  pk={book.pk}  order={book.bible_order}  "
            f"testament={book.testament.name if book.testament else '—'}"
        )

        # ── Core insert logic ────────────────────────────────────────────────
        inserted = updated = skipped = 0

        def _do_work():
            nonlocal inserted, updated, skipped

            for chapter_number in sorted(chapters_data.keys()):
                verses_raw = chapters_data[chapter_number]

                # De-duplicate: keep the last occurrence of each verse number
                verse_map: Dict[int, str] = {}
                duplicates: List[int]     = []
                for vd in verses_raw:
                    vnum = vd.get("verse")
                    if vnum is None:
                        continue
                    if vnum in verse_map:
                        duplicates.append(vnum)
                    verse_map[vnum] = vd.get("text", "").strip()

                if not verse_map:
                    self.stdout.write(
                        f"    Chapter {chapter_number}: no verses — skipped."
                    )
                    continue

                chapter_obj, ch_created = Chapter.objects.get_or_create(
                    book=book,
                    chapter_number=chapter_number,
                    defaults={"total_verses": len(verse_map)},
                )
                if chapter_obj.total_verses != len(verse_map):
                    chapter_obj.total_verses = len(verse_map)
                    if not dry_run:
                        chapter_obj.save(update_fields=["total_verses"])

                status   = "new" if ch_created else "existing"
                dup_note = (
                    f"  [merged duplicates: {sorted(set(duplicates))}]"
                    if duplicates else ""
                )
                self.stdout.write(
                    f"    Ch {chapter_number:>3} ({status}): "
                    f"{len(verse_map):>3} verses{dup_note}"
                )

                for verse_num, text_val in sorted(verse_map.items()):
                    verse_obj, _ = Verse.objects.get_or_create(
                        chapter=chapter_obj,
                        verse_number=verse_num,
                    )
                    vt, vt_created = VerseText.objects.get_or_create(
                        verse=verse_obj,
                        language=language,
                        defaults={"text": text_val},
                    )
                    if vt_created:
                        inserted += 1
                    elif overwrite and vt.text != text_val:
                        if not dry_run:
                            vt.text = text_val
                            vt.save(update_fields=["text"])
                        updated += 1
                    else:
                        skipped += 1

            # Keep book.total_chapters in sync
            actual_chapters = Chapter.objects.filter(book=book).count()
            if book.total_chapters != actual_chapters:
                book.total_chapters = actual_chapters
                if not dry_run:
                    book.save(update_fields=["total_chapters"])

        if dry_run:
            try:
                with transaction.atomic():
                    _do_work()
                    transaction.set_rollback(True)
            except Exception as exc:
                raise CommandError(f"Unexpected error during dry-run: {exc}")
        else:
            with transaction.atomic():
                _do_work()

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✔  {prefix}"
                f"inserted={inserted}  updated={updated}  skipped={skipped}"
            )
        )