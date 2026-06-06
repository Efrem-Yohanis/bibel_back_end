# core/urls/bible_urls.py
"""
Bible URLs - URL configuration for Bible endpoints
"""

from django.urls import path, re_path
from ..views.bible import (
    LanguagesView,
    TestamentsView,
    BooksByLanguageView,
    BooksByTestamentView,
    BookFullContentView,
    BookChaptersView,
    ChapterContentView,
    SpecificVerseView,
    SearchVersesView,
    VerseOfTheDayView
)
from ..views.audio_views import (
    RecordChapterCompletionView,
    UserAudioProgressView
)

urlpatterns = [
    # Language endpoints
    path('languages', LanguagesView.as_view(), name='languages'),
    path('testaments', TestamentsView.as_view(), name='testaments'),

    # Books endpoints
    path('books/by-language', BooksByLanguageView.as_view(), name='books-by-language'),
    path('testaments/<str:testament_name>/books', BooksByTestamentView.as_view(), name='books-by-testament'),

    # More specific routes must come before the generic book route
    re_path(r'^books/(?P<book_name>.+?)/chapters/(?P<chapter_number>\d+)/verses/(?P<verse_number>\d+)$',
            SpecificVerseView.as_view(), name='specific-verse'),
    re_path(r'^books/(?P<book_name>.+?)/chapters/(?P<chapter_number>\d+)$',
            ChapterContentView.as_view(), name='chapter-content'),
    re_path(r'^books/(?P<book_name>.+?)/chapters$',
            BookChaptersView.as_view(), name='book-chapters'),
    re_path(r'^books/(?P<book_name>.+?)/?$',
            BookFullContentView.as_view(), name='book-full-content'),

    # Audio progress endpoints
    path('audio/books/<int:book_id>/chapters/<int:chapter_number>/complete',
         RecordChapterCompletionView.as_view(), name='record-chapter-complete'),
    path('audio/books/<int:book_id>/progress',
         UserAudioProgressView.as_view(), name='user-audio-progress'),

    # Search and utility endpoints
    path('search', SearchVersesView.as_view(), name='search-verses'),
    path('verse-of-the-day', VerseOfTheDayView.as_view(), name='verse-of-the-day'),
]