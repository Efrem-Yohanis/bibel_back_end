"""
Management command to check books status in the database.
Run with: python manage.py check_books
"""

from django.core.management.base import BaseCommand
from core.models import Book, Testament, Chapter, Verse, VerseText, Language


class Command(BaseCommand):
    help = 'Check books status in the database'

    def handle(self, *args, **kwargs):

        # ==================== TOTAL BOOKS ====================
        total = Book.objects.count()
        self.stdout.write(f'\n=== Total Books in DB: {total} ===')

        # ==================== MISSING BIBLE ORDER ====================
        self.stdout.write('\n--- Books with bible_order=0 (not seeded) ---')
        missing_order = Book.objects.filter(bible_order=0).values('id', 'name')
        if missing_order:
            for b in missing_order:
                self.stdout.write(self.style.WARNING(f"  ✗ id={b['id']} | {b['name']}"))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ All books have bible_order set'))

        # ==================== MISSING TESTAMENT ====================
        self.stdout.write('\n--- Books with no testament ---')
        missing_testament = Book.objects.filter(testament__isnull=True).values('id', 'name')
        if missing_testament:
            for b in missing_testament:
                self.stdout.write(self.style.WARNING(f"  ✗ id={b['id']} | {b['name']}"))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ All books have testament set'))

        # ==================== ENGLISH NAMES ====================
        self.stdout.write('\n--- Books still with English names ---')
        english_books = Book.objects.filter(name__regex=r'^[A-Za-z]').values('id', 'name', 'bible_order')
        if english_books:
            for b in english_books:
                self.stdout.write(self.style.WARNING(
                    f"  ✗ id={b['id']} | order={b['bible_order']} | {b['name']}"
                ))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ All books have Amharic names'))

        # ==================== CHECK EXPECTED 66 BOOKS ====================
        self.stdout.write('\n--- Checking all 66 canonical books by bible_order ---')
        EXPECTED = [
            (1, 'Genesis/ዘፍጥረት'), (2, 'Exodus/ዘጸአት'), (3, 'Leviticus/ዘሌዋውያን'),
            (4, 'Numbers/ዘቍጥር'), (5, 'Deuteronomy/ዘዳግም'), (6, 'Joshua/ኢያሱ'),
            (7, 'Judges/መሳፍንት'), (8, 'Ruth/ሩት'), (9, '1 Samuel/1ኛ ሳሙኤል'),
            (10, '2 Samuel/2ኛ ሳሙኤል'), (11, '1 Kings/1ኛ ነገሥት'), (12, '2 Kings/2ኛ ነገሥት'),
            (13, '1 Chronicles/1ኛ ዜና መዋዕል'), (14, '2 Chronicles/2ኛ ዜና መዋዕል'),
            (15, 'Ezra/ዕዝራ'), (16, 'Nehemiah/ነህምያ'), (17, 'Esther/አስቴር'),
            (18, 'Job/ኢዮብ'), (19, 'Psalms/መዝሙር'), (20, 'Proverbs/ምሳሌ'),
            (21, 'Ecclesiastes/መክብብ'), (22, 'Song Of Solomon/መኃልየ መኃልይ'),
            (23, 'Isaiah/ኢሳይያስ'), (24, 'Jeremiah/ኤርምያስ'),
            (25, 'Lamentations/ሰቆቃወ ኤርምያስ'), (26, 'Ezekiel/ሕዝቅኤል'),
            (27, 'Daniel/ዳንኤል'), (28, 'Hosea/ሆሴዕ'), (29, 'Joel/ኢዩኤል'),
            (30, 'Amos/አሞጽ'), (31, 'Obadiah/አብድዩ'), (32, 'Jonah/ዮናስ'),
            (33, 'Micah/ሚክያስ'), (34, 'Nahum/ናሆም'), (35, 'Habakkuk/ዕንባቆም'),
            (36, 'Zephaniah/ሶፎንያስ'), (37, 'Haggai/ሐጌ'), (38, 'Zechariah/ዘካርያስ'),
            (39, 'Malachi/ሚልክያስ'), (40, 'Matthew/ማቴዎስ'), (41, 'Mark/ማርቆስ'),
            (42, 'Luke/ሉቃስ'), (43, 'John/ዮሐንስ'), (44, 'Acts/የሐዋርያት ሥራ'),
            (45, 'Romans/ሮሜ'), (46, '1 Corinthians/1ኛ ቆሮንቶስ'),
            (47, '2 Corinthians/2ኛ ቆሮንቶስ'), (48, 'Galatians/ገላትያ'),
            (49, 'Ephesians/ኤፌሶን'), (50, 'Philippians/ፊልጵስዩስ'),
            (51, 'Colossians/ቆላስይስ'), (52, '1 Thessalonians/1ኛ ተሰሎንቄ'),
            (53, '2 Thessalonians/2ኛ ተሰሎንቄ'), (54, '1 Timothy/1ኛ ጢሞቴዎስ'),
            (55, '2 Timothy/2ኛ ጢሞቴዎስ'), (56, 'Titus/ቲቶ'), (57, 'Philemon/ፊልሞና'),
            (58, 'Hebrews/ዕብራውያን'), (59, 'James/ያዕቆብ'), (60, '1 Peter/1ኛ ጴጥሮስ'),
            (61, '2 Peter/2ኛ ጴጥሮስ'), (62, '1 John/1ኛ ዮሐንስ'),
            (63, '2 John/2ኛ ዮሐንስ'), (64, '3 John/3ኛ ዮሐንስ'),
            (65, 'Jude/ይሁዳ'), (66, 'Revelation/ራዕይ'),
        ]

        missing = []
        for order, label in EXPECTED:
            book = Book.objects.filter(bible_order=order).first()
            if book:
                self.stdout.write(f'  ✓ {order:2}. {book.name}')
            else:
                missing.append((order, label))
                self.stdout.write(self.style.WARNING(f'  ✗ {order:2}. MISSING: {label}'))

        # ==================== CHAPTERS & VERSES PER BOOK ====================
        self.stdout.write('\n--- Chapters & Verses per book ---')
        books = Book.objects.order_by('bible_order').values('id', 'name', 'bible_order')
        for b in books:
            chapter_count = Chapter.objects.filter(book_id=b['id']).count()
            verse_count = Verse.objects.filter(chapter__book_id=b['id']).count()
            flag = '' if chapter_count > 0 else self.style.WARNING(' ⚠ NO CHAPTERS')
            self.stdout.write(
                f"  {b['bible_order']:2}. {b['name']:<25} | chapters={chapter_count} | verses={verse_count}{flag}"
            )

        # ==================== SUMMARY ====================
        self.stdout.write('\n=== SUMMARY ===')
        self.stdout.write(f'  Total books:         {total}')
        self.stdout.write(f'  Missing from 66:     {len(missing)}')
        self.stdout.write(f'  No bible_order:      {Book.objects.filter(bible_order=0).count()}')
        self.stdout.write(f'  No testament:        {Book.objects.filter(testament__isnull=True).count()}')
        self.stdout.write(f'  English names:       {Book.objects.filter(name__regex=chr(91) + "A-Za-z" + chr(93)).count()}')

        if missing:
            self.stdout.write(self.style.WARNING(
                f'\n  Missing books: {[f"{o}. {l}" for o, l in missing]}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\n  ✓ All 66 books present!'))