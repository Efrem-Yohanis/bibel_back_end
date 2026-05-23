"""
Bible Service - Manages Bible text retrieval for Django
FIXED: Chapter content, verse of the day, and URL encoding errors
"""

from django.db import models
from django.db.models import Count, Q
from django.utils import timezone
from typing import List, Dict, Optional, Any
from urllib.parse import unquote
import random
from ..models import (
    Language, Book, Testament, Chapter, Verse, VerseText
)


class BibleService:
    """Service for Bible text operations using Django ORM"""
    
    def __init__(self):
        pass
    
    # ==================== LANGUAGE METHODS ====================
    
    def get_languages(self) -> List[Dict]:
        """Get all active languages for Bible reading"""
        languages = Language.objects.filter(is_active=True).values(
            'id', 'code', 'name', 'native_name'
        ).order_by('id')
        
        return list(languages)
    
    def get_books_by_language(self, language_code: str = 'en') -> List[Dict]:
        """Get all books that have content in the specified language"""
        try:
            language = Language.objects.get(code=language_code)
        except Language.DoesNotExist:
            return []
        
        # Get books with verses in this language
        books = Book.objects.filter(
            chapters__verses__texts__language=language
        ).distinct().annotate(
            chapters_count=models.Count('chapters__id', distinct=True)
        ).select_related('testament').order_by('testament__id', 'id')
        
        return [
            {
                'id': book.id,
                'name': book.name,
                'testament': book.testament.name if book.testament else None,
                'chapters': getattr(book, 'chapters_count', 0)
            }
            for book in books
        ]
    
    # ==================== TESTAMENT METHODS ====================
    
    def get_testaments(self) -> List[Dict]:
        """Get list of all testaments (Old and New)"""
        testaments = Testament.objects.values('id', 'name').order_by('id')
        return list(testaments)
    
    def get_books_by_testament(self, testament_name: str) -> List[Dict]:
        """Get list of books by testament name (Old or New)"""
        books = Book.objects.filter(
            testament__name=testament_name
        ).annotate(
            chapters_count=models.Count('chapters__id', distinct=True),
            verses_count=models.Count('chapters__verses__id', distinct=True)
        ).values(
            'id', 'name', 'testament__name', 'chapters_count', 'verses_count'
        ).order_by('id')
        
        return list(books)
    
    def get_books_by_testament_with_language(self, testament_name: str, language_code: str = 'en') -> List[Dict]:
        """Get list of books by testament with chapter counts for specific language"""
        try:
            language = Language.objects.get(code=language_code)
        except Language.DoesNotExist:
            return []
        
        books = Book.objects.filter(
            testament__name=testament_name,
            chapters__verses__texts__language=language
        ).distinct().annotate(
            total_chapters=models.Count('chapters__id', distinct=True)
        ).values('id', 'name', 'total_chapters').order_by('id')
        
        return [
            {
                'book_id': book['id'],
                'book_name': book['name'],
                'total_chapters': book['total_chapters'] or 0
            }
            for book in books
        ]
    
    # ==================== BOOK CONTENT METHODS ====================
    
    def get_book_full_content(self, book_name: str, language_code: str = 'en') -> Dict:
        """Get full content of a specific book with book info"""
        try:
            book_name = unquote(book_name)
            language = Language.objects.get(code=language_code)
            
            # Get book info
            book = Book.objects.filter(
                Q(name__iexact=book_name) | 
                Q(name__icontains=book_name)
            ).annotate(
                total_chapters=models.Count('chapters__id', distinct=True),
                total_verses=models.Count('chapters__verses__id', distinct=True)
            ).select_related('testament').first()
            
            if not book:
                return {'error': f'Book "{book_name}" not found'}
            
            # Get all verses in this book for the specified language
            verses = VerseText.objects.filter(
                verse__chapter__book=book,
                language=language
            ).select_related(
                'verse__chapter'
            ).order_by(
                'verse__chapter__chapter_number',
                'verse__verse_number'
            ).values(
                'verse__chapter__chapter_number',
                'verse__verse_number',
                'text'
            )
            
            # Organize by chapter
            chapters_content = {}
            for verse in verses:
                chapter = verse['verse__chapter__chapter_number']
                if chapter not in chapters_content:
                    chapters_content[chapter] = []
                chapters_content[chapter].append({
                    'verse': verse['verse__verse_number'],
                    'text': verse['text']
                })
            
            return {
                'book_info': {
                    'id': book.id,
                    'name': book.name,
                    'testament': book.testament.name if book.testament else None,
                    'total_chapters': getattr(book, 'total_chapters', 0),
                    'total_verses': getattr(book, 'total_verses', 0)
                },
                'chapters': [
                    {
                        'chapter': chapter,
                        'verses': verses_data
                    }
                    for chapter, verses_data in sorted(chapters_content.items())
                ]
            }
            
        except Language.DoesNotExist:
            return {'error': f'Language "{language_code}" not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_book_chapters(self, book_name: str) -> Dict:
        """Get list of chapters in a book with verse counts"""
        try:
            book = Book.objects.filter(
                Q(name__iexact=book_name) | 
                Q(name__icontains=book_name)
            ).first()
            
            if not book:
                return {'error': f'Book "{book_name}" not found'}
            
            # Get chapters with verse counts
            chapters = Chapter.objects.filter(
                book=book
            ).annotate(
                verse_count=models.Count('verses__id')
            ).values('chapter_number', 'verse_count').order_by('chapter_number')
            
            return {
                'book': book.name,
                'total_chapters': chapters.count(),
                'chapters': list(chapters)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_book_chapters_with_language(self, book_name: str, language_code: str = 'en') -> Dict:
        """Get chapters of a book with verse counts for specific language"""
        try:
            book_name = unquote(book_name)
            
            book = Book.objects.filter(
                Q(name__iexact=book_name) | 
                Q(name__icontains=book_name)
            ).first()
            
            if not book:
                return {'error': f'Book "{book_name}" not found'}
            
            # Get chapters with verse counts (verses that exist in the specified language)
            chapters = Chapter.objects.filter(book=book).annotate(
                verse_count=models.Count(
                    'verses__texts',
                    filter=models.Q(verses__texts__language__code=language_code),
                    distinct=True
                )
            ).values('chapter_number', 'verse_count').order_by('chapter_number')
            
            # Convert to list of dictionaries with proper keys
            chapters_list = []
            for ch in chapters:
                chapters_list.append({
                    'chapter': ch['chapter_number'],
                    'verses': ch['verse_count'] or 0
                })
            
            return {
                'book_id': book.id,
                'book_name': book.name,
                'total_chapters': len(chapters_list),
                'chapters': chapters_list
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_chapters_content(self, book_name: str, language_code: str = 'en') -> Dict:
        """Get all chapters content of a book"""
        return self.get_book_full_content(book_name, language_code)
    
    # ==================== CHAPTER METHODS ====================
    
    def get_chapter_verses(self, book_name: str, chapter: int, language_code: str = 'en') -> Dict:
        """Get a specific chapter's verses"""
        try:
            book_name = unquote(book_name)
            language = Language.objects.get(code=language_code)
            
            book = Book.objects.filter(
                Q(name__iexact=book_name) | 
                Q(name__icontains=book_name)
            ).first()
            
            if not book:
                return {'error': f'Book "{book_name}" not found'}
            
            # Get the specific chapter
            try:
                chapter_obj = Chapter.objects.get(book=book, chapter_number=chapter)
            except Chapter.DoesNotExist:
                return {'error': f'Chapter {chapter} not found in {book.name}'}
            
            # Get verses for this chapter
            verses = VerseText.objects.filter(
                verse__chapter=chapter_obj,
                language=language
            ).select_related(
                'verse'
            ).order_by(
                'verse__verse_number'
            ).values(
                'verse__verse_number',
                'text'
            )
            
            if not verses.exists():
                return {'error': f'No verses found for {book.name} {chapter} in {language_code}'}
            
            return {
                'reference': f'{book.name} {chapter}',
                'book': book.name,
                'chapter': chapter,
                'total_verses': verses.count(),
                'verses': [
                    {
                        'verse': v['verse__verse_number'],
                        'text': v['text']
                    }
                    for v in verses
                ]
            }
            
        except Language.DoesNotExist:
            return {'error': f'Language "{language_code}" not found'}
        except Exception as e:
            return {'error': str(e)}
    
    # ==================== VERSE METHODS ====================
    
    def get_specific_verse(self, book_name: str, chapter: int, verse: int, language_code: str = 'en') -> Dict:
        """Get a specific verse"""
        try:
            book_name = unquote(book_name)
            language = Language.objects.get(code=language_code)
            
            book = Book.objects.filter(
                Q(name__iexact=book_name) | 
                Q(name__icontains=book_name)
            ).first()
            
            if not book:
                return {'error': f'Book "{book_name}" not found'}
            
            # Get verse
            try:
                verse_text = VerseText.objects.get(
                    verse__chapter__book=book,
                    verse__chapter__chapter_number=chapter,
                    verse__verse_number=verse,
                    language=language
                )
                
                return {
                    'reference': f'{book.name} {chapter}:{verse}',
                    'book': book.name,
                    'chapter': chapter,
                    'verse': verse,
                    'text': verse_text.text
                }
                
            except VerseText.DoesNotExist:
                return {
                    'error': f'Verse {book.name} {chapter}:{verse} not found'
                }
                
        except Language.DoesNotExist:
            return {'error': f'Language "{language_code}" not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_verse_all_languages(self, book_name: str, chapter: int, verse: int) -> Dict:
        """Get a verse in all available languages"""
        try:
            book_name = unquote(book_name)
            book = Book.objects.filter(
                Q(name__iexact=book_name) | 
                Q(name__icontains=book_name)
            ).first()
            
            if not book:
                return {'error': f'Book "{book_name}" not found'}
            
            # Get verse in all languages
            verse_texts = VerseText.objects.filter(
                verse__chapter__book=book,
                verse__chapter__chapter_number=chapter,
                verse__verse_number=verse
            ).select_related('language').values(
                'language__code',
                'language__name',
                'text'
            )
            
            if not verse_texts.exists():
                return {'error': f'Verse {book.name} {chapter}:{verse} not found'}
            
            result = {
                'reference': f'{book.name} {chapter}:{verse}',
                'verses': {}
            }
            
            for vt in verse_texts:
                result['verses'][vt['language__name']] = vt['text']
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    # ==================== SEARCH METHODS ====================
    
    def search_verses(self, query: str, language_code: str = 'en', limit: int = 50) -> List[Dict]:
        """Search for verses containing specific text"""
        try:
            language = Language.objects.get(code=language_code)
        except Language.DoesNotExist:
            return []
        
        verse_texts = VerseText.objects.filter(
            language=language,
            text__icontains=query
        ).select_related(
            'verse__chapter__book'
        ).values(
            'verse__chapter__book__name',
            'verse__chapter__chapter_number',
            'verse__verse_number',
            'text'
        )[:limit]
        
        return [
            {
                'reference': f"{vt['verse__chapter__book__name']} {vt['verse__chapter__chapter_number']}:{vt['verse__verse_number']}",
                'book': vt['verse__chapter__book__name'],
                'chapter': vt['verse__chapter__chapter_number'],
                'verse': vt['verse__verse_number'],
                'text': vt['text']
            }
            for vt in verse_texts
        ]
    
    def get_random_verse(self, language_code: str = 'en', testament: Optional[str] = None) -> Dict:
        """Get a random Bible verse"""
        try:
            language = Language.objects.get(code=language_code)
        except Language.DoesNotExist:
            return {'error': f'Language "{language_code}" not found'}
        
        # Build queryset
        queryset = VerseText.objects.filter(language=language)
        
        if testament:
            queryset = queryset.filter(
                verse__chapter__book__testament__name=testament
            )
        
        # Get random verse
        count = queryset.count()
        if count == 0:
            return {'error': 'No verses found'}
        
        # Get a random offset
        random_offset = random.randint(0, count - 1)
        
        verse_text = queryset.select_related(
            'verse__chapter__book'
        )[random_offset:random_offset+1].first()
        
        if not verse_text:
            return {'error': 'No verses found'}
        
        return {
            'reference': f"{verse_text.verse.chapter.book.name} {verse_text.verse.chapter.chapter_number}:{verse_text.verse.verse_number}",
            'book': verse_text.verse.chapter.book.name,
            'chapter': verse_text.verse.chapter.chapter_number,
            'verse': verse_text.verse.verse_number,
            'text': verse_text.text
        }
    
    def get_verse_of_the_day(self, language_code: str = 'en') -> Dict:
        """Get verse of the day (based on current date)"""
        from datetime import datetime
        day_of_year = datetime.now().timetuple().tm_yday
        
        try:
            language = Language.objects.get(code=language_code)
        except Language.DoesNotExist:
            return {'error': f'Language "{language_code}" not found'}
        
        # Get total count first
        total_verses = VerseText.objects.filter(language=language).count()
        
        if total_verses == 0:
            return {'error': f'No verses found for language {language_code}'}
        
        # Calculate offset based on day of year
        offset = day_of_year % total_verses
        
        # Get verse at that offset
        verse_text = VerseText.objects.filter(
            language=language
        ).select_related(
            'verse__chapter__book'
        ).order_by('id')[offset:offset+1].first()
        
        if not verse_text:
            return self.get_random_verse(language_code)
        
        return {
            'reference': f"{verse_text.verse.chapter.book.name} {verse_text.verse.chapter.chapter_number}:{verse_text.verse.verse_number}",
            'book': verse_text.verse.chapter.book.name,
            'chapter': verse_text.verse.chapter.chapter_number,
            'verse': verse_text.verse.verse_number,
            'text': verse_text.text
        }
    
    # ==================== STATISTICS METHODS ====================
    
    def get_bible_stats(self) -> Dict:
        """Get overall Bible statistics"""
        old_testament = self.get_testament_stats('Old')
        new_testament = self.get_testament_stats('New')
        
        return {
            'old_testament': old_testament,
            'new_testament': new_testament,
            'total': {
                'books': old_testament.get('books', 0) + new_testament.get('books', 0),
                'chapters': old_testament.get('chapters', 0) + new_testament.get('chapters', 0),
                'verses': old_testament.get('verses', 0) + new_testament.get('verses', 0)
            }
        }
    
    def get_testament_stats(self, testament: str) -> Dict:
        """Get statistics for a testament"""
        stats = Book.objects.filter(
            testament__name=testament
        ).aggregate(
            books=models.Count('id', distinct=True),
            chapters=models.Count('chapters__id', distinct=True),
            verses=models.Count('chapters__verses__id', distinct=True)
        )
        
        return {
            'books': stats['books'] or 0,
            'chapters': stats['chapters'] or 0,
            'verses': stats['verses'] or 0
        }