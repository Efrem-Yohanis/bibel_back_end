import os
import sys
import json
import re
from pathlib import Path

# Project root should be the folder containing manage.py
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')

import django
django.setup()

from django.db import transaction
from core.models import (
    Language,
    Book,
    Chapter,
    Level,
    Question,
    QuestionText,
    Option,
    OptionText,
    Explanation,
)


def get_chapter_number(verse_reference: str) -> int:
    match = re.search(r"(\d+)\s*[:]", verse_reference)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d+)", verse_reference)
    if match:
        return int(match.group(1))
    return 1


def get_or_create_level(level_number: int):
    level, _ = Level.objects.get_or_create(
        level_number=level_number,
        defaults={
            'name': f'Level {level_number}',
            'description': '',
        },
    )
    return level


@transaction.atomic
def import_amharic_questions(json_file: Path, language_code: str = 'am', book_name: str = 'Genesis'):
    with json_file.open('r', encoding='utf-8') as f:
        data = json.load(f)

    language, _ = Language.objects.get_or_create(
        code=language_code,
        defaults={
            'name': 'Amharic',
            'native_name': 'አማርኛ',
            'is_active': True,
        },
    )

    book, created = Book.objects.get_or_create(
        name__iexact=book_name,
        defaults={
            'name': book_name,
            'bible_order': 1,
            'total_chapters': 0,
        },
    )
    if not book.pk:
        book = Book.objects.get(name__iexact=book_name)

    questions_imported = 0

    for q in data.get('questions', []):
        chapter_number = get_chapter_number(q.get('verse_reference', ''))
        chapter, _ = Chapter.objects.get_or_create(
            book=book,
            chapter_number=chapter_number,
            defaults={'total_verses': 0},
        )

        level_num = 1
        level_value = q.get('level')
        if isinstance(level_value, int) or (isinstance(level_value, str) and level_value.isdigit()):
            level_num = int(level_value)
        level = get_or_create_level(level_num)

        correct_option = q.get('correct_answer') or q.get('correct_option') or 'A'
        question = Question.objects.create(
            book=book,
            chapter=chapter,
            level=level,
            correct_option=correct_option,
            verse_reference=q.get('verse_reference', ''),
        )

        QuestionText.objects.create(
            question=question,
            language=language,
            text=q.get('question', ''),
        )

        options_data = q.get('options', {}) or {}
        if isinstance(options_data, dict):
            items = list(options_data.items())
        else:
            items = []

        for label, text in items:
            if not label:
                continue
            option = Option.objects.create(
                question=question,
                label=str(label).strip(),
            )
            OptionText.objects.create(
                option=option,
                language=language,
                text=text or '',
            )

        if q.get('explanation'):
            Explanation.objects.create(
                question=question,
                language=language,
                text=q.get('explanation', ''),
            )

        questions_imported += 1

    print(f"Imported {questions_imported} questions for book '{book_name}' and language '{language_code}'.")


if __name__ == '__main__':
    json_path = Path(__file__).resolve().parent.parent / 'amharic_ge_q.json'
    import_amharic_questions(json_path, language_code='am', book_name='Genesis')
