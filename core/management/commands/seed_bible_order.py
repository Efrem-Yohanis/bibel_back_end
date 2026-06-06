# core/management/commands/seed_bible_order.py
from django.core.management.base import BaseCommand
from core.models import Book, Testament


class Command(BaseCommand):
    help = 'Seed bible_order and testament for all books'

    def handle(self, *args, **kwargs):
        # Create/get testaments
        old, _ = Testament.objects.get_or_create(name='Old')
        new, _ = Testament.objects.get_or_create(name='New')

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
            ('1 Corinthians', 46, new), ('2 Corinthians', 47, new), ('Galatians', 48, new),
            ('Ephesians', 49, new), ('Philippians', 50, new), ('Colossians', 51, new),
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

        self.stdout.write(self.style.SUCCESS(f'\nDone. Updated: {updated}, Not found: {len(not_found)}'))
        if not_found:
            self.stdout.write(self.style.WARNING(f'Missing: {not_found}'))

        still_zero = list(Book.objects.filter(bible_order=0).values_list('name', flat=True))
        if still_zero:
            self.stdout.write(self.style.WARNING(f'Still at 0: {still_zero}'))