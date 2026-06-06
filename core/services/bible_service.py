"""
Bible Service — manages Bible text retrieval and audio for Django.

Key improvements over the original:
  - Language resolved via ORM traversal (language__code=) instead of a
    separate Language.objects.get() call wherever possible.
  - get_chapter_audio fetches current/next/prev in one query.
  - get_verse_of_the_day uses a direct ORM offset instead of iterator+islice.
  - record_chapter_completion saves once instead of twice.
  - Bare `except Exception` replaced with specific exception types.
  - Redundant counting queries removed where model fields already hold the value.
  - Book names now returned in the requested language via BookName table.
"""

import random
from datetime import datetime
from itertools import islice
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from django.db import models
from django.db.models import Count, Prefetch, Q
from django.utils import timezone

from ..models import (
    Book, BookAudio, BookName, Chapter, ChapterAudio, DailyVerse,
    Language, Testament, User, UserBookProgress, Verse, VerseText,
)


class BibleService:
    """Service for Bible text and audio operations using Django ORM."""

    # ==================== LANGUAGE METHODS ====================

    def get_languages(self) -> List[Dict]:
        """Get all active languages for Bible reading."""
        return list(
            Language.objects.filter(is_active=True)
            .values('id', 'code', 'name', 'native_name')
            .order_by('id')
        )

    def get_books_by_language(self, language_code: str = 'en') -> Optional[List[Dict]]:
        """
        Get all books that have at least one verse translated into language_code.
        Returns None when the language does not exist.
        Book names are returned in the requested language (falls back to the
        default Book.name when no BookName entry exists for that language).
        """
        if not Language.objects.filter(code=language_code).exists():
            return None

        books = (
            Book.objects
            .filter(chapters__verses__texts__language__code=language_code)
            .distinct()
            .annotate(
                chapter_count=Count('chapters__id', distinct=True),
                audio_count=Count(
                    'chapter_audios',
                    filter=Q(
                        chapter_audios__language__code=language_code,
                        chapter_audios__is_available=True,
                    ),
                    distinct=True,
                ),
            )
            .prefetch_related(
                Prefetch(
                    'names',
                    queryset=BookName.objects.filter(
                        language__code=language_code
                    ).select_related('language'),
                )
            )
            .select_related('testament')
            .order_by('testament__id', 'bible_order')
        )

        return [
            {
                'id': book.id,
                'name': book.get_name(language_code),
                'testament': book.testament.name if book.testament else None,
                'chapters': book.chapter_count,
                'has_audio': book.audio_count > 0,
                'bible_order': book.bible_order,
            }
            for book in books
        ]

    # ==================== TESTAMENT METHODS ====================

    def get_testaments(self) -> List[Dict]:
        """Get list of all testaments (Old and New)."""
        return list(Testament.objects.values('id', 'name').order_by('id'))

    def get_books_by_testament(self, testament_name: str) -> List[Dict]:
        """Get books in a testament with chapter/verse counts."""
        books = (
            Book.objects
            .filter(testament__name=testament_name)
            .annotate(
                chapters_count=Count('chapters__id', distinct=True),
                verses_count=Count('chapters__verses__id', distinct=True),
            )
            .values(
                'id', 'name', 'testament__name',
                'chapters_count', 'verses_count', 'has_audio', 'bible_order',
            )
            .order_by('bible_order')
        )
        return list(books)

    def get_books_by_testament_with_language(
        self, testament_name: str, language_code: str = 'en'
    ) -> List[Dict]:
        """Get books in a testament with chapter counts for a specific language."""
        books = (
            Book.objects
            .filter(
                testament__name=testament_name,
                chapters__verses__texts__language__code=language_code,
            )
            .distinct()
            .annotate(total_chapters_count=Count('chapters__id', distinct=True))
            .prefetch_related(
                Prefetch(
                    'names',
                    queryset=BookName.objects.filter(
                        language__code=language_code
                    ).select_related('language'),
                )
            )
            .order_by('bible_order')
        )

        return [
            {
                'book_id': book.id,
                'book_name': book.get_name(language_code),
                'total_chapters': book.total_chapters_count or 0,
                'has_audio': book.has_audio,
                'bible_order': book.bible_order,
            }
            for book in books
        ]

    # ==================== AUDIO METHODS ====================

    def get_book_audio(self, book_id: int, language_code: str = 'en') -> Dict:
        """
        Get audio information for a specific book.
        Prefers full-book audio; falls back to chapter-level audio.
        """
        # Full-book audio
        book_audio = BookAudio.objects.filter(
            book_id=book_id,
            language__code=language_code,
            is_available=True,
        ).first()

        if book_audio:
            return {
                'has_audio': True,
                'audio_type': 'full_book',
                'audio_url': book_audio.get_audio_url(),
                'duration': book_audio.duration,
                'part_number': book_audio.part_number,
                'total_parts': book_audio.total_parts,
                'chapter_timestamps': book_audio.chapter_timestamps,
            }

        # Chapter-by-chapter audio
        chapter_audios = (
            ChapterAudio.objects
            .filter(book_id=book_id, language__code=language_code, is_available=True)
            .order_by('chapter_number')
        )

        if chapter_audios.exists():
            return {
                'has_audio': True,
                'audio_type': 'chapter_by_chapter',
                'chapters': [
                    {
                        'chapter': ca.chapter_number,
                        'audio_url': ca.get_audio_url(),
                        'duration': ca.duration,
                        'start_time': ca.start_time,
                    }
                    for ca in chapter_audios
                ],
            }

        return {'has_audio': False}

    def _get_book_audio_duration(
        self, book_id: int, language_code: str = 'en'
    ) -> Dict:
        """
        Return total and per-chapter audio duration for a book.
        Uses ORM traversal — no separate Language query.
        """
        book_audio = BookAudio.objects.filter(
            book_id=book_id,
            language__code=language_code,
            is_available=True,
        ).first()

        if book_audio and book_audio.duration:
            return {'total_seconds': book_audio.duration, 'chapter_seconds': {}}

        chapter_audios = ChapterAudio.objects.filter(
            book_id=book_id,
            language__code=language_code,
            is_available=True,
        )

        chapter_seconds = {ca.chapter_number: ca.duration or 0 for ca in chapter_audios}
        return {
            'total_seconds': sum(chapter_seconds.values()),
            'chapter_seconds': chapter_seconds,
        }

    def get_chapter_audio(
        self, book_id: int, chapter_number: int, language_code: str = 'en'
    ) -> Dict:
        """
        Get audio for a specific chapter, including prev/next availability.
        Fetches current, previous, and next chapters in a single query.
        """
        relevant = {
            ca.chapter_number: ca
            for ca in ChapterAudio.objects.filter(
                book_id=book_id,
                chapter_number__in=[chapter_number - 1, chapter_number, chapter_number + 1],
                language__code=language_code,
                is_available=True,
            )
        }

        current = relevant.get(chapter_number)
        if not current:
            return {
                'success': False,
                'has_audio': False,
                'message': 'No audio available for this chapter',
            }

        prev_audio = relevant.get(chapter_number - 1)
        next_audio = relevant.get(chapter_number + 1)

        return {
            'success': True,
            'has_audio': True,
            'audio_url': current.get_audio_url(),
            'duration': current.duration,
            'chapter_number': chapter_number,
            'prev_chapter_audio': prev_audio.chapter_number if prev_audio else None,
            'next_chapter_audio': next_audio.chapter_number if next_audio else None,
            'start_time': current.start_time,
        }

    def get_user_audio_progress(self, user_id: int, book_id: int) -> Dict:
        """Get user's audio progress for a specific book."""
        book = Book.objects.filter(id=book_id).select_related('testament').first()
        book_name = book.name if book else None
        testament = book.testament.name if book and book.testament else None

        try:
            progress = UserBookProgress.objects.get(user_id=user_id, book_id=book_id)
        except UserBookProgress.DoesNotExist:
            return {
                'success': True,
                'book_id': book_id,
                'book_name': book_name,
                'testament': testament,
                'current_chapter': 1,
                'current_verse': 1,
                'audio_current_position': 0,
                'audio_completed_chapters': [],
                'total_audio_duration': 0,
                'listened_audio_duration': 0,
                'remaining_audio_duration': 0,
                'audio_progress_percentage': 0,
                'completed': False,
                'progress_percentage': 0,
            }

        duration_info = self._get_book_audio_duration(book_id)
        total_duration = duration_info['total_seconds']
        chapter_durations = duration_info['chapter_seconds']

        listened_seconds = sum(
            chapter_durations.get(ch, 0) for ch in progress.audio_completed_chapters
        )
        current_chapter_duration = chapter_durations.get(progress.current_chapter, 0)
        listened_seconds += min(progress.audio_current_position or 0, current_chapter_duration)
        remaining_seconds = max(total_duration - listened_seconds, 0)
        audio_progress_pct = (
            int((listened_seconds / total_duration) * 100)
            if total_duration > 0
            else progress.get_audio_progress_percentage()
        )

        return {
            'success': True,
            'book_id': book_id,
            'book_name': book_name,
            'testament': testament,
            'current_chapter': progress.current_chapter,
            'current_verse': progress.current_verse,
            'audio_current_position': progress.audio_current_position,
            'audio_completed_chapters': progress.audio_completed_chapters,
            'total_audio_duration': total_duration,
            'listened_audio_duration': listened_seconds,
            'remaining_audio_duration': remaining_seconds,
            'audio_progress_percentage': audio_progress_pct,
            'completed': progress.completed,
            'progress_percentage': progress.get_audio_progress_percentage(),
        }

    # ==================== AUDIO PROGRESS METHODS ====================

    def record_chapter_completion(
        self, user_id: int, book_id: int, chapter_number: int, language_code: str = 'en'
    ) -> Dict:
        """Record that a user completed a chapter audio."""
        try:
            book = Book.objects.get(id=book_id)
            user = User.objects.get(id=user_id)
        except (Book.DoesNotExist, User.DoesNotExist) as e:
            return {'success': False, 'error': str(e)}

        next_chapter = chapter_number + 1 if chapter_number < book.total_chapters else chapter_number

        progress, _ = UserBookProgress.objects.get_or_create(
            user=user,
            book=book,
            defaults={'current_chapter': next_chapter, 'current_verse': 1},
        )

        if chapter_number not in (progress.audio_completed_chapters or []):
            completed = sorted(set(progress.audio_completed_chapters or []) | {chapter_number})
            progress.audio_completed_chapters = completed

            if chapter_number < book.total_chapters:
                progress.current_chapter = chapter_number + 1

            progress.last_audio_listened = timezone.now()
            progress.completed = len(completed) >= book.total_chapters
            progress.save()  # single save

        pct = (
            (len(progress.audio_completed_chapters) / book.total_chapters) * 100
            if book.total_chapters
            else 0
        )

        return {
            'success': True,
            'completed_chapters': progress.audio_completed_chapters,
            'current_chapter': progress.current_chapter,
            'next_chapter': chapter_number + 1 if chapter_number < book.total_chapters else None,
            'book_completed': progress.completed,
            'progress_percentage': pct,
        }

    def get_user_audio_status(self, user_id: int, book_id: int) -> Dict:
        """Get user's audio progress for a book."""
        try:
            progress = UserBookProgress.objects.select_related('book').get(
                user_id=user_id, book_id=book_id
            )
        except UserBookProgress.DoesNotExist:
            return {
                'success': True,
                'completed_chapters': [],
                'current_chapter': 1,
                'book_completed': False,
                'progress_percentage': 0,
            }

        total = progress.book.total_chapters
        pct = (len(progress.audio_completed_chapters) / total * 100) if total else 0

        return {
            'success': True,
            'completed_chapters': progress.audio_completed_chapters,
            'current_chapter': progress.current_chapter,
            'book_completed': progress.completed,
            'progress_percentage': pct,
        }

    def update_audio_progress(
        self,
        user_id: int,
        book_id: int,
        chapter_number: int,
        current_position: Optional[int] = None,
        completed_chapter: Optional[int] = None,
        language_code: str = 'en',
    ) -> Dict:
        """Update user's audio progress for a book."""
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return {'success': False, 'error': f'Book {book_id} not found'}

        progress, _ = UserBookProgress.objects.get_or_create(
            user_id=user_id,
            book_id=book_id,
            defaults={'current_chapter': chapter_number, 'current_verse': 1},
        )

        progress.current_chapter = chapter_number

        if current_position is not None:
            progress.audio_current_position = current_position
            progress.last_audio_listened = timezone.now()

        if completed_chapter is not None:
            completed = set(progress.audio_completed_chapters or [])
            completed.add(completed_chapter)
            progress.audio_completed_chapters = sorted(completed)

        progress.completed = len(progress.audio_completed_chapters) >= book.total_chapters
        progress.save()

        duration_info = self._get_book_audio_duration(book_id, language_code)
        total_duration = duration_info['total_seconds']
        chapter_durations = duration_info['chapter_seconds']

        listened_seconds = sum(
            chapter_durations.get(ch, 0) for ch in progress.audio_completed_chapters
        ) + min(
            progress.audio_current_position or 0,
            chapter_durations.get(progress.current_chapter, 0),
        )
        remaining_seconds = max(total_duration - listened_seconds, 0)
        audio_progress_pct = (
            int((listened_seconds / total_duration) * 100)
            if total_duration > 0
            else progress.get_audio_progress_percentage()
        )

        return {
            'success': True,
            'book_id': book_id,
            'book_name': book.name,
            'testament': book.testament.name if book.testament else None,
            'current_chapter': progress.current_chapter,
            'audio_current_position': progress.audio_current_position,
            'audio_completed_chapters': progress.audio_completed_chapters,
            'total_audio_duration': total_duration,
            'listened_audio_duration': listened_seconds,
            'remaining_audio_duration': remaining_seconds,
            'audio_progress_percentage': audio_progress_pct,
            'completed': progress.completed,
            'progress_percentage': progress.get_audio_progress_percentage(),
        }

    # ==================== BOOK CONTENT METHODS ====================

    def _lookup_book(self, book_name: str, language_code: str = 'am') -> Optional[Book]:
        """
        Book lookup: tries the BookName table for the given language first,
        then falls back to a case-insensitive match on Book.name.
        """
        # Try translated name first
        book_name_entry = (
            BookName.objects
            .filter(
                Q(name__iexact=book_name) | Q(name__icontains=book_name),
                language__code=language_code,
            )
            .select_related('book__testament')
            .first()
        )
        if book_name_entry:
            return book_name_entry.book

        # Fall back to the stored Book.name (Amharic default)
        return (
            Book.objects
            .filter(Q(name__iexact=book_name) | Q(name__icontains=book_name))
            .select_related('testament')
            .first()
        )

    def get_book_full_content(self, book_name: str, language_code: str = 'en') -> Dict:
        """
        Get the full content of a book: metadata, audio info, and all verses
        organised by chapter.
        """
        book_name = unquote(book_name)
        book = self._lookup_book(book_name, language_code)
        if not book:
            return {'error': f'Book "{book_name}" not found'}

        if not Language.objects.filter(code=language_code).exists():
            return {'error': f'Language "{language_code}" not found'}

        # Fetch all chapter audio in one query
        chapter_audios = ChapterAudio.objects.filter(
            book=book,
            language__code=language_code,
            is_available=True,
        ).values('chapter_number', 'audio_url', 'duration')

        audio_lookup: Dict[int, Dict] = {
            ca['chapter_number']: {
                'has_audio': True,
                'audio_url': ca['audio_url'],
                'audio_duration': ca['duration'],
            }
            for ca in chapter_audios
        }

        # Fetch all verses in one query, ordered for sequential iteration
        verses = (
            VerseText.objects
            .filter(verse__chapter__book=book, language__code=language_code)
            .select_related('verse__chapter')
            .order_by('verse__chapter__chapter_number', 'verse__verse_number')
            .values('verse__chapter__chapter_number', 'verse__verse_number', 'text')
        )

        # Group verses by chapter
        chapters_content: List[Dict] = []
        current_chapter: Optional[int] = None
        current_verses: List[Dict] = []

        def _flush_chapter(ch_num: int, ch_verses: List[Dict]) -> None:
            audio_data = audio_lookup.get(ch_num, {
                'has_audio': False, 'audio_url': None, 'audio_duration': None,
            })
            chapters_content.append({
                'chapter': ch_num,
                'has_audio': audio_data['has_audio'],
                'audio_url': audio_data['audio_url'],
                'audio_duration': audio_data['audio_duration'],
                'verses': ch_verses,
            })

        for verse in verses:
            ch_num = verse['verse__chapter__chapter_number']
            if current_chapter != ch_num:
                if current_chapter is not None:
                    _flush_chapter(current_chapter, current_verses)
                current_chapter = ch_num
                current_verses = []
            current_verses.append({
                'verse': verse['verse__verse_number'],
                'text': verse['text'],
            })

        if current_chapter is not None:
            _flush_chapter(current_chapter, current_verses)

        # Full-book audio check
        book_audio = BookAudio.objects.filter(
            book=book, language__code=language_code, is_available=True
        ).first()

        has_any_audio = bool(audio_lookup) or book_audio is not None
        audio_info: Dict = {
            'has_audio': has_any_audio,
            'type': (
                'full_book' if book_audio
                else 'chapter_by_chapter' if audio_lookup
                else 'none'
            ),
            'chapters_with_audio': len(audio_lookup),
        }
        if book_audio:
            audio_info['book_audio_url'] = book_audio.get_audio_url()
            audio_info['book_duration'] = book_audio.duration

        displayed_name = book.get_name(language_code)

        return {
            'book_info': {
                'id': book.id,
                'name': displayed_name,
                'testament': book.testament.name if book.testament else None,
                'total_chapters': book.total_chapters,
                'total_verses': Verse.objects.filter(chapter__book=book).count(),
                'has_audio': book.has_audio or has_any_audio,
            },
            'audio_info': audio_info,
            'chapters': chapters_content,
        }

    def get_book_chapters(self, book_name: str) -> Dict:
        """Get list of chapters in a book with verse counts."""
        book = self._lookup_book(book_name)
        if not book:
            return {'error': f'Book "{book_name}" not found'}

        chapters = (
            Chapter.objects.filter(book=book)
            .annotate(verse_count=Count('verses__id'))
            .values('chapter_number', 'verse_count')
            .order_by('chapter_number')
        )
        chapters_list = list(chapters)

        return {
            'book': book.name,
            'book_id': book.id,
            'total_chapters': len(chapters_list),
            'has_audio': book.has_audio,
            'chapters': chapters_list,
        }

    def get_book_chapters_with_language(
        self, book_name: str, language_code: str = 'en'
    ) -> Dict:
        """Get chapters of a book with verse counts for a specific language."""
        book_name = unquote(book_name)
        book = self._lookup_book(book_name, language_code)
        if not book:
            return {'error': f'Book "{book_name}" not found'}

        chapters = (
            Chapter.objects.filter(book=book)
            .annotate(
                verse_count=Count(
                    'verses__texts',
                    filter=Q(verses__texts__language__code=language_code),
                    distinct=True,
                )
            )
            .values('chapter_number', 'verse_count')
            .order_by('chapter_number')
        )

        chapters_list = [
            {'chapter': ch['chapter_number'], 'verses': ch['verse_count'] or 0}
            for ch in chapters
        ]

        return {
            'book_id': book.id,
            'book_name': book.get_name(language_code),
            'total_chapters': len(chapters_list),
            'has_audio': book.has_audio,
            'chapters': chapters_list,
        }

    def get_chapters_content(self, book_name: str, language_code: str = 'en') -> Dict:
        """Alias for get_book_full_content."""
        return self.get_book_full_content(book_name, language_code)

    # ==================== CHAPTER METHODS ====================

    def get_chapter_verses(
        self, book_name: str, chapter: int, language_code: str = 'en'
    ) -> Dict:
        """Get a specific chapter's verses."""
        book_name = unquote(book_name)
        chapter = int(chapter)

        book = self._lookup_book(book_name, language_code)
        if not book:
            return {'error': f'Book "{book_name}" not found'}

        if not Language.objects.filter(code=language_code).exists():
            return {'error': f'Language "{language_code}" not found'}

        try:
            chapter_obj = Chapter.objects.get(book=book, chapter_number=chapter)
        except Chapter.DoesNotExist:
            return {'error': f'Chapter {chapter} not found in {book.get_name(language_code)}'}

        verses = (
            VerseText.objects
            .filter(verse__chapter=chapter_obj, language__code=language_code)
            .select_related('verse')
            .order_by('verse__verse_number')
            .values('verse__verse_number', 'text')
        )

        if not verses.exists():
            return {'error': f'No verses found for {book.get_name(language_code)} {chapter} in {language_code}'}

        audio_info = self.get_chapter_audio(book.id, chapter, language_code)
        displayed_name = book.get_name(language_code)

        return {
            'reference': f'{displayed_name} {chapter}',
            'book': displayed_name,
            'book_id': book.id,
            'chapter': chapter,
            'total_verses': verses.count(),
            'has_audio': audio_info.get('has_audio', False),
            'audio_url': audio_info.get('audio_url') if audio_info.get('has_audio') else None,
            'verses': [
                {'verse': v['verse__verse_number'], 'text': v['text']} for v in verses
            ],
        }

    # ==================== VERSE METHODS ====================

    def get_specific_verse(
        self, book_name: str, chapter: int, verse: int, language_code: str = 'en'
    ) -> Dict:
        """Get a specific verse."""
        book_name = unquote(book_name)
        book = self._lookup_book(book_name, language_code)
        if not book:
            return {'error': f'Book "{book_name}" not found'}

        try:
            verse_text = VerseText.objects.get(
                verse__chapter__book=book,
                verse__chapter__chapter_number=chapter,
                verse__verse_number=verse,
                language__code=language_code,
            )
        except VerseText.DoesNotExist:
            return {'error': f'Verse {book.get_name(language_code)} {chapter}:{verse} not found in {language_code}'}

        displayed_name = book.get_name(language_code)

        return {
            'reference': f'{displayed_name} {chapter}:{verse}',
            'book': displayed_name,
            'book_id': book.id,
            'chapter': chapter,
            'verse': verse,
            'text': verse_text.text,
        }

    def get_verse_all_languages(self, book_name: str, chapter: int, verse: int) -> Dict:
        """Get a verse in all available languages."""
        book_name = unquote(book_name)
        book = self._lookup_book(book_name)
        if not book:
            return {'error': f'Book "{book_name}" not found'}

        verse_texts = (
            VerseText.objects
            .filter(
                verse__chapter__book=book,
                verse__chapter__chapter_number=chapter,
                verse__verse_number=verse,
            )
            .select_related('language')
            .values('language__code', 'language__name', 'text')
        )

        if not verse_texts.exists():
            return {'error': f'Verse {book.name} {chapter}:{verse} not found'}

        return {
            'reference': f'{book.name} {chapter}:{verse}',
            'verses': {vt['language__name']: vt['text'] for vt in verse_texts},
        }

    # ==================== SEARCH METHODS ====================

    def search_verses(
        self, query: str, language_code: str = 'en', limit: int = 50
    ) -> List[Dict]:
        """Search for verses containing specific text."""
        verse_texts = (
            VerseText.objects
            .filter(language__code=language_code, text__icontains=query)
            .select_related('verse__chapter__book')
            .values(
                'verse__chapter__book__name',
                'verse__chapter__book__id',
                'verse__chapter__chapter_number',
                'verse__verse_number',
                'text',
            )[:limit]
        )

        # For search results, also resolve the translated book name
        book_ids = list({vt['verse__chapter__book__id'] for vt in verse_texts})
        book_name_map = {
            bn.book_id: bn.name
            for bn in BookName.objects.filter(
                book_id__in=book_ids,
                language__code=language_code,
            )
        }

        return [
            {
                'reference': (
                    f"{book_name_map.get(vt['verse__chapter__book__id'], vt['verse__chapter__book__name'])} "
                    f"{vt['verse__chapter__chapter_number']}:{vt['verse__verse_number']}"
                ),
                'book': book_name_map.get(vt['verse__chapter__book__id'], vt['verse__chapter__book__name']),
                'book_id': vt['verse__chapter__book__id'],
                'chapter': vt['verse__chapter__chapter_number'],
                'verse': vt['verse__verse_number'],
                'text': vt['text'],
            }
            for vt in verse_texts
        ]

    def get_random_verse(
        self, language_code: str = 'en', testament: Optional[str] = None
    ) -> Dict:
        """Get a random Bible verse."""
        queryset = VerseText.objects.filter(language__code=language_code)

        if testament:
            queryset = queryset.filter(
                verse__chapter__book__testament__name=testament
            )

        count = queryset.count()
        if count == 0:
            return {'error': 'No verses found'}

        verse_text = (
            queryset
            .select_related('verse__chapter__book')
            [random.randint(0, count - 1)]
        )

        displayed_name = verse_text.verse.chapter.book.get_name(language_code)

        return {
            'reference': (
                f"{displayed_name} "
                f"{verse_text.verse.chapter.chapter_number}:{verse_text.verse.verse_number}"
            ),
            'book': displayed_name,
            'book_id': verse_text.verse.chapter.book.id,
            'chapter': verse_text.verse.chapter.chapter_number,
            'verse': verse_text.verse.verse_number,
            'text': verse_text.text,
        }

    def get_verse_of_the_day(self, language_code: str = 'en') -> Dict:
        """
        Get the verse of the day from the pre-curated DailyVerse pool.
        Selection is deterministic: index = day_of_year % total_daily_verses.
        Falls back to any translated verse when the pool is empty.
        """
        day_of_year = datetime.now().timetuple().tm_yday

        total_daily_verses = DailyVerse.objects.count()

        if total_daily_verses == 0:
            # Fallback: pick from all translated verses
            verse_text_qs = VerseText.objects.filter(language__code=language_code)
            if not verse_text_qs.exists():
                verse_text_qs = VerseText.objects.filter(language__code='en')
            if not verse_text_qs.exists():
                return {'error': 'No daily verses configured and no translated verses available.'}

            offset = day_of_year % verse_text_qs.count()
            verse_text = (
                verse_text_qs
                .select_related('verse__chapter__book')
                [offset]
            )
            displayed_name = verse_text.verse.chapter.book.get_name(language_code)
            return {
                'reference': (
                    f"{displayed_name} "
                    f"{verse_text.verse.chapter.chapter_number}:{verse_text.verse.verse_number}"
                ),
                'book': displayed_name,
                'book_id': verse_text.verse.chapter.book.id,
                'chapter': verse_text.verse.chapter.chapter_number,
                'verse': verse_text.verse.verse_number,
                'text': verse_text.text,
                'category': None,
                'category_slug': None,
            }

        # Direct ORM offset — no iterator/islice needed
        offset = day_of_year % total_daily_verses
        daily_verse = (
            DailyVerse.objects
            .select_related('verse__chapter__book', 'category')
            .order_by('id')
            [offset]
        )

        # Resolve text in requested language, fall back to English
        try:
            text = daily_verse.verse.texts.get(language__code=language_code).text
        except VerseText.DoesNotExist:
            try:
                text = daily_verse.verse.texts.get(language__code='en').text
            except VerseText.DoesNotExist:
                text = '[Verse text not available]'

        displayed_name = daily_verse.verse.chapter.book.get_name(language_code)

        return {
            'reference': (
                f"{displayed_name} "
                f"{daily_verse.verse.chapter.chapter_number}:{daily_verse.verse.verse_number}"
            ),
            'book': displayed_name,
            'book_id': daily_verse.verse.chapter.book.id,
            'chapter': daily_verse.verse.chapter.chapter_number,
            'verse': daily_verse.verse.verse_number,
            'text': text,
            'category': daily_verse.category.title,
            'category_slug': daily_verse.category.slug,
        }

    # ==================== STATISTICS METHODS ====================

    def get_bible_stats(self) -> Dict:
        """Get overall Bible statistics."""
        old = self.get_testament_stats('Old')
        new = self.get_testament_stats('New')
        return {
            'old_testament': old,
            'new_testament': new,
            'total': {
                'books': old['books'] + new['books'],
                'chapters': old['chapters'] + new['chapters'],
                'verses': old['verses'] + new['verses'],
            },
        }

    def get_testament_stats(self, testament: str) -> Dict:
        """Get statistics for a testament."""
        stats = Book.objects.filter(testament__name=testament).aggregate(
            books=Count('id', distinct=True),
            chapters=Count('chapters__id', distinct=True),
            verses=Count('chapters__verses__id', distinct=True),
        )
        return {
            'books': stats['books'] or 0,
            'chapters': stats['chapters'] or 0,
            'verses': stats['verses'] or 0,
        }

    def get_audio_stats(self) -> Dict:
        """Get statistics about audio availability."""
        total_books = Book.objects.count()
        books_with_audio = Book.objects.filter(has_audio=True).count()
        return {
            'total_books': total_books,
            'books_with_audio': books_with_audio,
            'books_without_audio': total_books - books_with_audio,
            'chapter_audio_files': ChapterAudio.objects.filter(is_available=True).count(),
            'book_audio_files': BookAudio.objects.filter(is_available=True).count(),
            'audio_coverage_percentage': (
                books_with_audio / total_books * 100 if total_books > 0 else 0
            ),
        }