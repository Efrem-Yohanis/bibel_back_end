# core/urls/bible_urls.py
"""
Bible URLs — URL configuration for all Bible and audio endpoints.

Ordering rules:
  1. Fixed-segment utility paths first (search, stats, verse-of-the-day, random-verse)
     so they are never accidentally matched by a parameterised book-name segment.
  2. Audio resource paths next (no book-name ambiguity).
  3. Parameterised Bible-content paths last, ordered most-specific → least-specific
     so Django matches the longest pattern first.

All paths use a consistent NO trailing slash convention.
Set APPEND_SLASH = False in settings.py (or add trailing slashes everywhere — just be consistent).
"""

from django.urls import path

from ..views.bible import (
    AudioStatsView,
    BibleStatsView,
    BookChaptersView,
    BookFullContentView,
    BooksByLanguageView,
    BooksByTestamentView,
    ChapterContentView,
    LanguagesView,
    RandomVerseView,
    SearchVersesView,
    SpecificVerseView,
    TestamentsView,
    VerseOfTheDayView,
    BookAudioView,
    ChapterAudioView,
    UserAudioProgressView,
    UpdateAudioProgressView,
)
from ..views.audio_views import RecordChapterCompletionView

urlpatterns = [

    # ------------------------------------------------------------------
    # 1. Fixed utility endpoints  (must be declared before any path that
    #    uses <str:book_name> to prevent accidental matches)
    # ------------------------------------------------------------------
    path('languages', LanguagesView.as_view(), name='languages'),
    path('testaments', TestamentsView.as_view(), name='testaments'),
    path('books/by-language', BooksByLanguageView.as_view(), name='books-by-language'),
    path('search', SearchVersesView.as_view(), name='search-verses'),
    path('verse-of-the-day', VerseOfTheDayView.as_view(), name='verse-of-the-day'),
    path('random-verse', RandomVerseView.as_view(), name='random-verse'),
    path('stats', BibleStatsView.as_view(), name='bible-stats'),

    # ------------------------------------------------------------------
    # 2. Testament-scoped book list
    # ------------------------------------------------------------------
    path(
        'testaments/<str:testament_name>/books',
        BooksByTestamentView.as_view(),
        name='books-by-testament',
    ),

    # ------------------------------------------------------------------
    # 3. Audio endpoints  (fixed-structure paths, no book-name segment)
    # ------------------------------------------------------------------
    path(
        'audio/stats',
        AudioStatsView.as_view(),
        name='audio-stats',
    ),
    path(
        'audio/books/<int:book_id>/progress',
        UserAudioProgressView.as_view(),
        name='user-audio-progress',
    ),
    path(
        'audio/books/<int:book_id>/progress/update',
        UpdateAudioProgressView.as_view(),
        name='update-audio-progress',
    ),
    path(
        'audio/books/<int:book_id>/chapters/<int:chapter_number>/complete',
        RecordChapterCompletionView.as_view(),
        name='record-chapter-complete',
    ),
    path(
        'audio/books/<int:book_id>/chapters/<int:chapter_number>',
        ChapterAudioView.as_view(),
        name='chapter-audio',
    ),
    path(
        'audio/books/<int:book_id>',
        BookAudioView.as_view(),
        name='book-audio',
    ),

    # ------------------------------------------------------------------
    # 4. Bible content — ordered most-specific → least-specific.
    #    <str:book_name> matches a single path segment (no slashes),
    #    so plain path() converters are safe and re_path is not needed.
    # ------------------------------------------------------------------
    path(
        'books/<str:book_name>/chapters/<int:chapter_number>/verses/<int:verse_number>',
        SpecificVerseView.as_view(),
        name='specific-verse',
    ),
    path(
        'books/<str:book_name>/chapters/<int:chapter_number>',
        ChapterContentView.as_view(),
        name='chapter-content',
    ),
    path(
        'books/<str:book_name>/chapters',
        BookChaptersView.as_view(),
        name='book-chapters',
    ),
    path(
        'books/<str:book_name>',
        BookFullContentView.as_view(),
        name='book-full-content',
    ),
]