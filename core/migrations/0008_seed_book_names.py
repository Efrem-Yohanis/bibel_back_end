from django.db import migrations

# english_name → bible_order (matches the canonical Amharic books with order 1-66)
ENGLISH_TO_ORDER = {
    'Genesis': 1, 'Exodus': 2, 'Leviticus': 3, 'Numbers': 4,
    'Deuteronomy': 5, 'Joshua': 6, 'Judges': 7, 'Ruth': 8,
    '1 Samuel': 9, '2 Samuel': 10, '1 Kings': 11, '2 Kings': 12,
    '1 Chronicles': 13, '2 Chronicles': 14, 'Ezra': 15, 'Nehemiah': 16,
    'Esther': 17, 'Job': 18, 'Psalms': 19, 'Proverbs': 20,
    'Ecclesiastes': 21, 'Song of Solomon': 22, 'Isaiah': 23, 'Jeremiah': 24,
    'Lamentations': 25, 'Ezekiel': 26, 'Daniel': 27, 'Hosea': 28,
    'Joel': 29, 'Amos': 30, 'Obadiah': 31, 'Jonah': 32,
    'Micah': 33, 'Nahum': 34, 'Habakkuk': 35, 'Zephaniah': 36,
    'Haggai': 37, 'Zechariah': 38, 'Malachi': 39, 'Matthew': 40,
    'Mark': 41, 'Luke': 42, 'John': 43, 'Acts': 44,
    'Romans': 45, '1 Corinthians': 46, '2 Corinthians': 47, 'Galatians': 48,
    'Ephesians': 49, 'Philippians': 50, 'Colossians': 51,
    '1 Thessalonians': 52, '2 Thessalonians': 53, '1 Timothy': 54,
    '2 Timothy': 55, 'Titus': 56, 'Philemon': 57, 'Hebrews': 58,
    'James': 59, '1 Peter': 60, '2 Peter': 61, '1 John': 62,
    '2 John': 63, '3 John': 64, 'Jude': 65, 'Revelation': 66,
}

# bible_order → {lang_code: name}
BOOK_NAMES = {
    1:  {'am': 'ዘፍጥረት',       'en': 'Genesis',         'or': 'Uumaa',              'ti': 'ዘፍጥረት'},
    2:  {'am': 'ዘጸአት',         'en': 'Exodus',          'or': 'Baqqisaa',           'ti': 'ዘጸኣት'},
    3:  {'am': 'ዘሌዋውያን',      'en': 'Leviticus',       'or': 'Leewwootaa',         'ti': 'ዘሌዋውያን'},
    4:  {'am': 'ዘቍጥር',        'en': 'Numbers',         'or': 'Lakkoofsa',          'ti': 'ዘኁልቍ'},
    5:  {'am': 'ዘዳግም',        'en': 'Deuteronomy',     'or': 'Seera Lammaffaa',    'ti': 'ዘዳግም'},
    6:  {'am': 'ኢያሱ',         'en': 'Joshua',          'or': 'Yoosuwaa',           'ti': 'የያሱ'},
    7:  {'am': 'መሳፍንት',       'en': 'Judges',          'or': 'Abbootii Murtii',    'ti': 'መሳፍንት'},
    8:  {'am': 'ሩት',          'en': 'Ruth',            'or': 'Ruutii',             'ti': 'ሩት'},
    9:  {'am': '1ኛ ሳሙኤል',     'en': '1 Samuel',        'or': "1 Samuu'eel",        'ti': '1 ሳሙኤል'},
    10: {'am': '2ኛ ሳሙኤል',     'en': '2 Samuel',        'or': "2 Samuu'eel",        'ti': '2 ሳሙኤል'},
    11: {'am': '1ኛ ነገሥት',     'en': '1 Kings',         'or': '1 Mootota',          'ti': '1 ነገስት'},
    12: {'am': '2ኛ ነገሥት',     'en': '2 Kings',         'or': '2 Mootota',          'ti': '2 ነገስት'},
    13: {'am': '1ኛ ዜና መዋዕል',  'en': '1 Chronicles',    'or': '1 Seenaa',           'ti': '1 ዜና መዋዕል'},
    14: {'am': '2ኛ ዜና መዋዕል',  'en': '2 Chronicles',    'or': '2 Seenaa',           'ti': '2 ዜና መዋዕል'},
    15: {'am': 'ዕዝራ',         'en': 'Ezra',            'or': 'Eziraa',             'ti': 'ዕዝራ'},
    16: {'am': 'ነህምያ',        'en': 'Nehemiah',        'or': 'Neheemiyaa',         'ti': 'ነህምያ'},
    17: {'am': 'አስቴር',        'en': 'Esther',          'or': 'Esteer',             'ti': 'አስቴር'},
    18: {'am': 'ኢዮብ',         'en': 'Job',             'or': 'Iyyoob',             'ti': 'ኢዮብ'},
    19: {'am': 'መዝሙር',        'en': 'Psalms',          'or': 'Faarfannaa',         'ti': 'መዝሙር'},
    20: {'am': 'ምሳሌ',         'en': 'Proverbs',        'or': 'Makmaaksa',          'ti': 'ምሳሌ'},
    21: {'am': 'መክብብ',        'en': 'Ecclesiastes',    'or': "Maa'ii Dubbii",      'ti': 'መክብብ'},
    22: {'am': 'መኃልየ መኃልይ',   'en': 'Song of Solomon', 'or': 'Faaruu Faaruuwwan',  'ti': 'መኃልየ መኃልይ'},
    23: {'am': 'ኢሳይያስ',       'en': 'Isaiah',          'or': 'Isaayyaas',          'ti': 'ኢሳይያስ'},
    24: {'am': 'ኤርምያስ',       'en': 'Jeremiah',        'or': 'Ermiyaas',           'ti': 'ኤርምያስ'},
    25: {'am': 'ሰቆቃወ ኤርምያስ',  'en': 'Lamentations',    'or': 'Booichaa',           'ti': 'ሰቆቃወ ኤርምያስ'},
    26: {'am': 'ሕዝቅኤል',       'en': 'Ezekiel',         'or': 'Hezqeel',            'ti': 'ሕዝቅኤል'},
    27: {'am': 'ዳንኤል',        'en': 'Daniel',          'or': 'Daaniyeel',          'ti': 'ዳንኤል'},
    28: {'am': 'ሆሴዕ',         'en': 'Hosea',           'or': 'Hoosea',             'ti': 'ሆሴዕ'},
    29: {'am': 'ኢዩኤል',        'en': 'Joel',            'or': 'Yooel',              'ti': 'ኢዩኤል'},
    30: {'am': 'አሞጽ',         'en': 'Amos',            'or': 'Aamoos',             'ti': 'አሞጽ'},
    31: {'am': 'አብድዩ',        'en': 'Obadiah',         'or': 'Obadiyaa',           'ti': 'አብድዩ'},
    32: {'am': 'ዮናስ',         'en': 'Jonah',           'or': 'Yoonaas',            'ti': 'ዮናስ'},
    33: {'am': 'ሚክያስ',        'en': 'Micah',           'or': 'Miikaa',             'ti': 'ሚክያስ'},
    34: {'am': 'ናሆም',         'en': 'Nahum',           'or': 'Naahuum',            'ti': 'ናሆም'},
    35: {'am': 'ዕንባቆም',       'en': 'Habakkuk',        'or': 'Habaquuq',           'ti': 'ዕንባቆም'},
    36: {'am': 'ሶፎንያስ',       'en': 'Zephaniah',       'or': 'Xafaniyaas',         'ti': 'ሶፎንያስ'},
    37: {'am': 'ሐጌ',          'en': 'Haggai',          'or': 'Haggaay',            'ti': 'ሐጌ'},
    38: {'am': 'ዘካርያስ',       'en': 'Zechariah',       'or': 'Zakariyaas',         'ti': 'ዘካርያስ'},
    39: {'am': 'ሚልክያስ',       'en': 'Malachi',         'or': 'Malaakii',           'ti': 'ሚልክያስ'},
    40: {'am': 'ማቴዎስ',        'en': 'Matthew',         'or': 'Maatewoos',          'ti': 'ማቴዎስ'},
    41: {'am': 'ማርቆስ',        'en': 'Mark',            'or': 'Maarqoos',           'ti': 'ማርቆስ'},
    42: {'am': 'ሉቃስ',         'en': 'Luke',            'or': 'Luuqaas',            'ti': 'ሉቃስ'},
    43: {'am': 'ዮሐንስ',        'en': 'John',            'or': 'Yohannis',           'ti': 'ዮሃንስ'},
    44: {'am': 'የሐዋርያት ሥራ',   'en': 'Acts',            'or': 'Hojii Ergamootaa',   'ti': 'ግብሪ ሃዋርያት'},
    45: {'am': 'ሮሜ',          'en': 'Romans',          'or': 'Roomaa',             'ti': 'ሮሜ'},
    46: {'am': '1ኛ ቆሮንቶስ',    'en': '1 Corinthians',   'or': '1 Qorontos',         'ti': '1 ቆሮንቶስ'},
    47: {'am': '2ኛ ቆሮንቶስ',    'en': '2 Corinthians',   'or': '2 Qorontos',         'ti': '2 ቆሮንቶስ'},
    48: {'am': 'ገላትያ',        'en': 'Galatians',       'or': 'Galaatiyaa',         'ti': 'ገላትያ'},
    49: {'am': 'ኤፌሶን',        'en': 'Ephesians',       'or': 'Efesoon',            'ti': 'ኤፌሶን'},
    50: {'am': 'ፊልጵስዩስ',      'en': 'Philippians',     'or': 'Filiiphisiyuus',     'ti': 'ፊልጵስዩስ'},
    51: {'am': 'ቆላስይስ',       'en': 'Colossians',      'or': 'Qolasiyoos',         'ti': 'ቆላስይስ'},
    52: {'am': '1ኛ ተሰሎንቄ',    'en': '1 Thessalonians', 'or': '1 Tesalooniiqe',     'ti': '1 ተሰሎንቄ'},
    53: {'am': '2ኛ ተሰሎንቄ',    'en': '2 Thessalonians', 'or': '2 Tesalooniiqe',     'ti': '2 ተሰሎንቄ'},
    54: {'am': '1ኛ ጢሞቴዎስ',    'en': '1 Timothy',       'or': '1 Ximootewoos',      'ti': '1 ጢሞቴዎስ'},
    55: {'am': '2ኛ ጢሞቴዎስ',    'en': '2 Timothy',       'or': '2 Ximootewoos',      'ti': '2 ጢሞቴዎስ'},
    56: {'am': 'ቲቶ',          'en': 'Titus',           'or': 'Xiitoosa',           'ti': 'ቲቶ'},
    57: {'am': 'ፊልሞና',        'en': 'Philemon',        'or': 'Filimoon',           'ti': 'ፊልሞና'},
    58: {'am': 'ዕብራውያን',      'en': 'Hebrews',         'or': 'Ibroota',            'ti': 'ዕብራውያን'},
    59: {'am': 'ያዕቆብ',        'en': 'James',           'or': 'Yaaqoob',            'ti': 'ያዕቆብ'},
    60: {'am': '1ኛ ጴጥሮስ',     'en': '1 Peter',         'or': '1 Phexroos',         'ti': '1 ጴጥሮስ'},
    61: {'am': '2ኛ ጴጥሮስ',     'en': '2 Peter',         'or': '2 Phexroos',         'ti': '2 ጴጥሮስ'},
    62: {'am': '1ኛ ዮሐንስ',     'en': '1 John',          'or': '1 Yohannis',         'ti': '1 ዮሃንስ'},
    63: {'am': '2ኛ ዮሐንስ',     'en': '2 John',          'or': '2 Yohannis',         'ti': '2 ዮሃንስ'},
    64: {'am': '3ኛ ዮሐንስ',     'en': '3 John',          'or': '3 Yohannis',         'ti': '3 ዮሃንስ'},
    65: {'am': 'ይሁዳ',         'en': 'Jude',            'or': 'Yihuudaa',           'ti': 'ይሁዳ'},
    66: {'am': 'ራዕይ',         'en': 'Revelation',      'or': 'Muldhannoo',         'ti': 'ራዕይ'},
}

# Correct total_chapters per bible_order
CORRECT_CHAPTERS = {
    1: 50, 2: 40, 3: 27, 4: 36, 5: 34, 6: 24, 7: 21, 8: 4,
    9: 31, 10: 24, 11: 22, 12: 25, 13: 29, 14: 36, 15: 10,
    16: 13, 17: 10, 18: 42, 19: 150, 20: 31, 21: 12, 22: 8,
    23: 66, 24: 52, 25: 5, 26: 48, 27: 12, 28: 14, 29: 3,
    30: 9, 31: 1, 32: 4, 33: 7, 34: 3, 35: 3, 36: 3,
    37: 2, 38: 14, 39: 4, 40: 28, 41: 16, 42: 24, 43: 21,
    44: 28, 45: 16, 46: 16, 47: 13, 48: 6, 49: 6, 50: 4,
    51: 4, 52: 5, 53: 3, 54: 6, 55: 4, 56: 3, 57: 1,
    58: 13, 59: 5, 60: 5, 61: 3, 62: 5, 63: 1, 64: 1,
    65: 1, 66: 22,
}


def seed_forward(apps, schema_editor):
    Book = apps.get_model('core', 'Book')
    BookName = apps.get_model('core', 'BookName')
    ChapterAudio = apps.get_model('core', 'ChapterAudio')
    Chapter = apps.get_model('core', 'Chapter')
    Language = apps.get_model('core', 'Language')

    languages = {l.code: l for l in Language.objects.filter(code__in=['am', 'en', 'or', 'ti'])}
    en_lang = languages.get('en')

    # canonical books: bible_order 1-66 (Amharic names)
    canonical = {b.bible_order: b for b in Book.objects.filter(bible_order__gte=1)}

    # duplicate books: bible_order=0 (English names, created by import script)
    duplicates = {b.name: b for b in Book.objects.filter(bible_order=0)}

    audio_moved = 0
    audio_skipped = 0
    books_deleted = 0
    names_created = 0

    # ── STEP 1: Move ChapterAudio from duplicate English books → canonical books ──
    for en_name, dup_book in duplicates.items():
        order = ENGLISH_TO_ORDER.get(en_name)
        if not order:
            print(f'  WARNING: No order mapping for "{en_name}", skipping')
            continue

        canon = canonical.get(order)
        if not canon:
            print(f'  WARNING: No canonical book for order {order} ({en_name}), skipping')
            continue

        for audio in ChapterAudio.objects.filter(book=dup_book, language=en_lang):
            conflict = ChapterAudio.objects.filter(
                book=canon,
                chapter_number=audio.chapter_number,
                language=en_lang,
            ).exists()

            if conflict:
                audio_skipped += 1
                continue

            # Re-point chapter FK to the canonical book's chapter if it exists
            chapter = Chapter.objects.filter(
                book=canon,
                chapter_number=audio.chapter_number
            ).first()

            audio.book = canon
            audio.chapter = chapter
            audio.save()
            audio_moved += 1

    # ── STEP 2: Fix total_chapters & has_audio on canonical books ──
    for order, canon in canonical.items():
        correct = CORRECT_CHAPTERS.get(order, canon.total_chapters)
        has_audio = ChapterAudio.objects.filter(book=canon, is_available=True).exists()
        canon.total_chapters = correct
        canon.has_audio = has_audio
        canon.save()

    # ── STEP 3: Delete duplicate English books (now empty of audio) ──
    for en_name, dup_book in duplicates.items():
        remaining = ChapterAudio.objects.filter(book=dup_book).count()
        if remaining > 0:
            print(f'  WARNING: Cannot delete "{en_name}" (id={dup_book.id}) — still has {remaining} audio rows')
            continue
        dup_book.delete()
        books_deleted += 1

    # ── STEP 4: Seed BookName for all 4 languages on canonical books ──
    for order, canon in canonical.items():
        names = BOOK_NAMES.get(order)
        if not names:
            print(f'  WARNING: No name data for order {order}')
            continue
        for lang_code, name in names.items():
            lang = languages.get(lang_code)
            if not lang:
                continue
            _, created = BookName.objects.get_or_create(
                book=canon,
                language=lang,
                defaults={'name': name},
            )
            if created:
                names_created += 1

    print(f'\nDone!')
    print(f'  Audio rows moved  : {audio_moved}')
    print(f'  Audio rows skipped: {audio_skipped}')
    print(f'  Books deleted     : {books_deleted}')
    print(f'  BookNames created : {names_created}')


def seed_reverse(apps, schema_editor):
    # Just clear BookName rows; we can't undo the book merge safely
    apps.get_model('core', 'BookName').objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_bookname'),
    ]

    operations = [
        migrations.RunPython(seed_forward, seed_reverse),
    ]