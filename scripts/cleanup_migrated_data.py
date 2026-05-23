#!/usr/bin/env python
"""
Clean up duplicate data after migration - SIMPLIFIED VERSION
Run: python scripts/cleanup_migrated_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')

import django
django.setup()

from core.models import (
    Testament, Book, Chapter, Verse, VerseText,
    Question, QuestionText, Option, OptionText, Explanation
)
from django.db import transaction
from django.db.models import Count


def cleanup_testaments():
    """Remove duplicate testaments"""
    print("\n📖 Cleaning up Testaments...")
    
    # Keep only Old and New
    old_test, _ = Testament.objects.get_or_create(name='Old')
    new_test, _ = Testament.objects.get_or_create(name='New')
    
    # Delete others
    deleted = Testament.objects.exclude(id__in=[old_test.id, new_test.id]).delete()
    print(f"  ✅ Deleted {deleted[0]} duplicate testaments")
    print(f"  ✅ Remaining: {Testament.objects.count()}")
    return old_test, new_test


def cleanup_books():
    """Remove duplicate books - keep first occurrence"""
    print("\n📚 Cleaning up Books...")
    
    # Get unique book names
    unique_books = {}
    to_delete = []
    
    for book in Book.objects.select_related('testament'):
        key = (book.name.lower(), book.testament_id)
        if key not in unique_books:
            unique_books[key] = book
        else:
            to_delete.append(book)
    
    for book in to_delete:
        # Delete related chapters (they will cascade)
        book.delete()
    
    print(f"  ✅ Deleted {len(to_delete)} duplicate books")
    print(f"  ✅ Remaining: {Book.objects.count()}")


def cleanup_chapters():
    """Remove duplicate chapters"""
    print("\n📑 Cleaning up Chapters...")
    
    duplicates = Chapter.objects.values('book_id', 'chapter_number').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    deleted = 0
    for dup in duplicates:
        chapters = Chapter.objects.filter(
            book_id=dup['book_id'],
            chapter_number=dup['chapter_number']
        )
        first = chapters.first()
        to_delete = chapters.exclude(id=first.id)
        deleted += to_delete.delete()[0]
    
    print(f"  ✅ Deleted {deleted} duplicate chapters")
    print(f"  ✅ Remaining: {Chapter.objects.count()}")


def cleanup_verses():
    """Remove duplicate verses"""
    print("\n📜 Cleaning up Verses...")
    
    duplicates = Verse.objects.values('chapter_id', 'verse_number').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    deleted = 0
    for dup in duplicates:
        verses = Verse.objects.filter(
            chapter_id=dup['chapter_id'],
            verse_number=dup['verse_number']
        )
        first = verses.first()
        to_delete = verses.exclude(id=first.id)
        deleted += to_delete.delete()[0]
    
    print(f"  ✅ Deleted {deleted} duplicate verses")
    print(f"  ✅ Remaining: {Verse.objects.count()}")


def cleanup_verse_texts():
    """Remove duplicate verse texts"""
    print("\n🌐 Cleaning up Verse Texts...")
    
    duplicates = VerseText.objects.values('verse_id', 'language_id').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    deleted = 0
    for dup in duplicates:
        texts = VerseText.objects.filter(
            verse_id=dup['verse_id'],
            language_id=dup['language_id']
        )
        first = texts.first()
        to_delete = texts.exclude(id=first.id)
        deleted += to_delete.delete()[0]
    
    print(f"  ✅ Deleted {deleted} duplicate verse texts")
    print(f"  ✅ Remaining: {VerseText.objects.count()}")


def cleanup_questions():
    """Remove duplicate questions"""
    print("\n❓ Cleaning up Questions...")
    
    duplicates = Question.objects.values('book_id', 'chapter_id', 'verse_reference').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    deleted = 0
    for dup in duplicates:
        questions = Question.objects.filter(
            book_id=dup['book_id'],
            chapter_id=dup['chapter_id'],
            verse_reference=dup['verse_reference']
        )
        first = questions.first()
        to_delete = questions.exclude(id=first.id)
        
        for q in to_delete:
            # Delete related data
            QuestionText.objects.filter(question=q).delete()
            Explanation.objects.filter(question=q).delete()
            for opt in Option.objects.filter(question=q):
                OptionText.objects.filter(option=opt).delete()
                opt.delete()
            q.delete()
            deleted += 1
    
    print(f"  ✅ Deleted {deleted} duplicate questions")
    print(f"  ✅ Remaining: {Question.objects.count()}")


@transaction.atomic
def cleanup_all():
    """Run all cleanup"""
    print("=" * 60)
    print("🧹 STARTING DATA CLEANUP")
    print("=" * 60)
    
    cleanup_testaments()
    cleanup_books()
    cleanup_chapters()
    cleanup_verses()
    cleanup_verse_texts()
    cleanup_questions()
    
    print("\n" + "=" * 60)
    print("✅ CLEANUP COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    response = input("\nContinue? (yes/no): ")
    if response.lower() == 'yes':
        cleanup_all()
    else:
        print("Cancelled.")