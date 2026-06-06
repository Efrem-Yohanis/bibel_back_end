"""
Management command to seed bible_order, testament, and Amharic book names.
Run with: python manage.py seed_bible_order
"""

from django.core.management.base import BaseCommand
from core.models import Book, Testament


class Command(BaseCommand):
    help = 'Seed bible_order, testament, and Amharic names for all books'

    def handle(self, *args, **kwargs):

        # ==================== STEP 1: TESTAMENTS ====================
        self.stdout.write('\n--- Step 1: Creating Testaments ---')
        old, created = Testament.objects.get_or_create(name='Old')
        self.stdout.write(f"  {'Created' if created else 'Found'} Old Testament")
        new, created = Testament.objects.get_or_create(name='New')
        self.stdout.write(f"  {'Created' if created else 'Found'} New Testament")

        # ==================== STEP 2: BIBLE ORDER + TESTAMENT ====================
        self.stdout.write('\n--- Step 2: Seeding bible_order and testament ---')

        BIBLE_ORDER = [
            ('Genesis', 1, old), ('Exodus', 2, old), ('Leviticus', 3, old),
            ('Numbers', 4, old), ('Deuteronomy', 5, old), ('Joshua', 6, old),
            ('Judges', 7, old), ('Ruth', 8, old), ('1 Samuel', 9, old),
            ('2 Samuel', 10, old), ('1 Kings', 11, old), ('2 Kings', 12, old),
            ('1 Chronicles', 13, old), ('2 Chronicles', 14, old), ('Ezra', 15, old),
            ('Nehemiah', 16, old), ('Esther', 17, old), ('Job', 18, old),
            ('Psalms', 19, old), ('Proverbs', 20, old), ('Ecclesiastes', 21, old),
            ('Song Of Solomon', 22, old), ('Isaiah', 23, old), ('Jeremiah', 24, old),
            ('Lamentations', 25, old), ('Ezekiel', 26, old), ('Daniel', 27, old),
            ('Hosea', 28, old), ('Joel', 29, old), ('Amos', 30, old),
            ('Obadiah', 31, old), ('Jonah', 32, old), ('Micah', 33, old),
            ('Nahum', 34, old), ('Habakkuk', 35, old), ('Zephaniah', 36, old),
            ('Haggai', 37, old), ('Zechariah', 38, old), ('Malachi', 39, old),
            ('Matthew', 40, new), ('Mark', 41, new), ('Luke', 42, new),
            ('John', 43, new), ('Acts', 44, new), ('Romans', 45, new),
            ('1 Corinthians', 46, new), ('2 Corinthians', 47, new),
            ('Galatians', 48, new), ('Ephesians', 49, new),
            ('Philippians', 50, new), ('Colossians', 51, new),
            ('1 Thessalonians', 52, new), ('2 Thessalonians', 53, new),
            ('1 Timothy', 54, new), ('2 Timothy', 55, new), ('Titus', 56, new),
            ('Philemon', 57, new), ('Hebrews', 58, new), ('James', 59, new),
            ('1 Peter', 60, new), ('2 Peter', 61, new), ('1 John', 62, new),
            ('2 John', 63, new), ('3 John', 64, new), ('Jude', 65, new),
            ('Revelation', 66, new),
        ]

        updated = 0
        not_found = []

        for name, order, testament in BIBLE_ORDER:
            count = Book.objects.filter(name__iexact=name).update(
                bible_order=order,
                testament=testament
            )
            if count:
                updated += count
                self.stdout.write(f'  ✓ {order}. {name}')
            else:
                not_found.append(name)
                self.stdout.write(self.style.WARNING(f'  ✗ NOT FOUND: {name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nStep 2 Done. Updated: {updated}, Not found: {len(not_found)}'
        ))
        if not_found:
            self.stdout.write(self.style.WARNING(f'Missing books: {not_found}'))

        # ==================== STEP 3: AMHARIC NAMES ====================
        self.stdout.write('\n--- Step 3: Updating book names to Amharic ---')

        AMHARIC_NAMES = [
            # Old Testament - match by English first (in case not yet renamed)
            ('Genesis', 'ዘፍጥረት'),
            ('Exodus', 'ዘጸአት'),
            ('Leviticus', 'ዘሌዋውያን'),
            ('Numbers', 'ዘቍጥር'),
            ('Deuteronomy', 'ዘዳግም'),
            ('Joshua', 'ኢያሱ'),
            ('Judges', 'መሳፍንት'),
            ('Ruth', 'ሩት'),
            ('1 Samuel', '1ኛ ሳሙኤል'),
            ('2 Samuel', '2ኛ ሳሙኤል'),
            ('1 Kings', '1ኛ ነገሥት'),
            ('2 Kings', '2ኛ ነገሥት'),
            ('1 Chronicles', '1ኛ ዜና መዋዕል'),
            ('2 Chronicles', '2ኛ ዜና መዋዕል'),
            ('Ezra', 'ዕዝራ'),
            ('Nehemiah', 'ነህምያ'),
            ('Esther', 'አስቴር'),
            ('Job', 'ኢዮብ'),
            ('Psalms', 'መዝሙር'),
            ('Proverbs', 'ምሳሌ'),
            ('Ecclesiastes', 'መክብብ'),
            ('Song Of Solomon', 'መኃልየ መኃልይ'),
            ('Isaiah', 'ኢሳይያስ'),
            ('Jeremiah', 'ኤርምያስ'),
            ('Lamentations', 'ሰቆቃወ ኤርምያስ'),
            ('Ezekiel', 'ሕዝቅኤል'),
            ('Daniel', 'ዳንኤል'),
            ('Hosea', 'ሆሴዕ'),
            ('Joel', 'ኢዩኤል'),
            ('Amos', 'አሞጽ'),
            ('Obadiah', 'አብድዩ'),
            ('Jonah', 'ዮናስ'),
            ('Micah', 'ሚክያስ'),
            ('Nahum', 'ናሆም'),
            ('Habakkuk', 'ዕንባቆም'),
            ('Zephaniah', 'ሶፎንያስ'),
            ('Haggai', 'ሐጌ'),
            ('Zechariah', 'ዘካርያስ'),
            ('Malachi', 'ሚልክያስ'),
            # New Testament
            ('Matthew', 'ማቴዎስ'),
            ('Mark', 'ማርቆስ'),
            ('Luke', 'ሉቃስ'),
            ('John', 'ዮሐንስ'),
            ('Acts', 'የሐዋርያት ሥራ'),
            ('Romans', 'ሮሜ'),
            ('1 Corinthians', '1ኛ ቆሮንቶስ'),
            ('2 Corinthians', '2ኛ ቆሮንቶስ'),
            ('Galatians', 'ገላትያ'),
            ('Ephesians', 'ኤፌሶን'),
            ('Philippians', 'ፊልጵስዩስ'),
            ('Colossians', 'ቆላስይስ'),
            ('1 Thessalonians', '1ኛ ተሰሎንቄ'),
            ('2 Thessalonians', '2ኛ ተሰሎንቄ'),
            ('1 Timothy', '1ኛ ጢሞቴዎስ'),
            ('2 Timothy', '2ኛ ጢሞቴዎስ'),
            ('Titus', 'ቲቶ'),
            ('Philemon', 'ፊልሞና'),
            ('Hebrews', 'ዕብራውያን'),
            ('James', 'ያዕቆብ'),
            ('1 Peter', '1ኛ ጴጥሮስ'),
            ('2 Peter', '2ኛ ጴጥሮስ'),
            ('1 John', '1ኛ ዮሐንስ'),
            ('2 John', '2ኛ ዮሐንስ'),
            ('3 John', '3ኛ ዮሐንስ'),
            ('Jude', 'ይሁዳ'),
            ('Revelation', 'ራዕይ'),
        ]

        renamed = 0
        skipped = []

        for english_name, amharic_name in AMHARIC_NAMES:
            count = Book.objects.filter(name__iexact=english_name).update(name=amharic_name)
            if count:
                renamed += count
                self.stdout.write(f'  ✓ {english_name} → {amharic_name}')
            else:
                skipped.append(english_name)

        self.stdout.write(self.style.SUCCESS(
            f'\nStep 3 Done. Renamed: {renamed}, Already Amharic or not found: {len(skipped)}'
        ))
        if skipped:
            self.stdout.write(self.style.WARNING(f'Skipped (already renamed or missing): {skipped}'))

        # ==================== FINAL CHECK ====================
        self.stdout.write('\n--- Final Check ---')

        still_english = list(
            Book.objects.filter(name__regex=r'^[A-Za-z]').values_list('name', flat=True)
        )
        still_zero = list(
            Book.objects.filter(bible_order=0).values_list('name', flat=True)
        )
        no_testament = list(
            Book.objects.filter(testament__isnull=True).values_list('name', flat=True)
        )

        if still_english:
            self.stdout.write(self.style.WARNING(f'Still English: {still_english}'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ All books have Amharic names'))

        if still_zero:
            self.stdout.write(self.style.WARNING(f'Still bible_order=0: {still_zero}'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ All books have bible_order set'))

        if no_testament:
            self.stdout.write(self.style.WARNING(f'No testament: {no_testament}'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ All books have testament set'))

        self.stdout.write(self.style.SUCCESS('\n=== All done! ==='))