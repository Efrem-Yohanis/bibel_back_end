"""
Bible URLs - URL configuration for Bible endpoints
"""

from django.urls import path
from ..views.bible import (
    LanguagesView,
    BooksByLanguageView,
    BooksByTestamentView,
    BookFullContentView,
    BookChaptersView,
    ChapterContentView,
    SpecificVerseView,
    SearchVersesView,
    VerseOfTheDayView
)

urlpatterns = [
    # Language endpoints
    path('languages', LanguagesView.as_view(), name='languages'),
    
    # Books endpoints
    path('books/by-language', BooksByLanguageView.as_view(), name='books-by-language'),
    path('testaments/<str:testament_name>/books', BooksByTestamentView.as_view(), name='books-by-testament'),
    path('books/<str:book_name>', BookFullContentView.as_view(), name='book-full-content'),
    path('books/<str:book_name>/chapters', BookChaptersView.as_view(), name='book-chapters'),
    
    # Chapter endpoints
    path('books/<str:book_name>/chapters/<int:chapter_number>', ChapterContentView.as_view(), name='chapter-content'),
    
    # Verse endpoints
    path('books/<str:book_name>/chapters/<int:chapter_number>/verses/<int:verse_number>', 
         SpecificVerseView.as_view(), name='specific-verse'),
    
    # Search and utility endpoints
    path('search', SearchVersesView.as_view(), name='search-verses'),
    path('verse-of-the-day', VerseOfTheDayView.as_view(), name='verse-of-the-day'),
    # Removed: random endpoint
]