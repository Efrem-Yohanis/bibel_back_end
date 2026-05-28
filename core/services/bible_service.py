"""
Bible Service - Manages Bible text retrieval and audio for Django
FIXED: Chapter content, verse of the day, URL encoding errors, and audio support
"""

from django.db import models
from django.db.models import Count, Q
from django.utils import timezone
from typing import List, Dict, Optional, Any
from urllib.parse import unquote
import random
from ..models import (
    Language, Book, Testament, Chapter, Verse, VerseText,
    BookAudio, ChapterAudio, UserBookProgress
)
from ..models import User


class BibleService:
    """Service for Bible text and audio operations using Django ORM"""
    
    def __init__(self):
        pass
    
    # ==================== LANGUAGE METHODS ====================
    
    def get_languages(self) -> List[Dict]:
        """Get all active languages for Bible reading"""
        languages = Language.objects.filter(is_active=True).values(
            'id', 'code', 'name', 'native_name'
        ).order_by('id')
        
        return list(languages)
    
# In your bible_service.py, look for any .annotate() calls

    def get_books_by_language(self, language_code: str = 'en') -> List[Dict]:
        try:
            language = Language.objects.get(code=language_code)
        except Language.DoesNotExist:
            return []
        
        # Change this:
        books = Book.objects.filter(
            chapters__verses__texts__language=language
        ).distinct().annotate(
            chapter_count=models.Count('chapters__id', distinct=True)  # ← Use different name
        ).select_related('testament').order_by('testament__id', 'bible_order')
        
        return [
            {
                'id': book.id,
                'name': book.name,
                'testament': book.testament.name if book.testament else None,
                'chapters': getattr(book, 'chapter_count', 0),  # ← Use the annotated name
                'has_audio': book.has_audio,
                'bible_order': book.bible_order
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
            'id', 'name', 'testament__name', 'chapters_count', 'verses_count', 'has_audio', 'bible_order'
        ).order_by('bible_order')
        
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
            total_chapters_count=models.Count('chapters__id', distinct=True)
        ).values('id', 'name', 'total_chapters_count', 'has_audio', 'bible_order').order_by('bible_order')
        
        return [
            {
                'book_id': book['id'],
                'book_name': book['name'],
                'total_chapters': book['total_chapters_count'] or 0,
                'has_audio': book['has_audio'],
                'bible_order': book['bible_order']
            }
            for book in books
        ]
    
    # ==================== AUDIO METHODS ====================
    
    def get_book_audio(self, book_id: int, language_code: str = 'en') -> Dict:
        """Get audio information for a specific book"""
        try:
            language = Language.objects.get(code=language_code)
            
            # Check for book-level audio
            book_audio = BookAudio.objects.filter(
                book_id=book_id,
                language=language,
                is_available=True
            ).first()
            
            if book_audio:
                return {
                    'has_audio': True,
                    'audio_type': 'full_book',
                    'audio_url': book_audio.get_audio_url(),
                    'duration': book_audio.duration,
                    'part_number': book_audio.part_number,
                    'total_parts': book_audio.total_parts,
                    'chapter_timestamps': book_audio.chapter_timestamps
                }
            
            # Check for chapter-level audio
            chapter_audios = ChapterAudio.objects.filter(
                book_id=book_id,
                language=language,
                is_available=True
            ).order_by('chapter_number')
            
            if chapter_audios.exists():
                return {
                    'has_audio': True,
                    'audio_type': 'chapter_by_chapter',
                    'chapters': [
                        {
                            'chapter': ca.chapter_number,
                            'audio_url': ca.get_audio_url(),
                            'duration': ca.duration,
                            'start_time': ca.start_time
                        }
                        for ca in chapter_audios
                    ]
                }
            
            return {'has_audio': False}
            
        except Language.DoesNotExist:
            return {'has_audio': False, 'error': f'Language {language_code} not found'}
    
    def get_chapter_audio(self, book_id: int, chapter_number: int, language_code: str = 'en') -> Dict:
        """Get audio for a specific chapter"""
        try:
            language = Language.objects.get(code=language_code)
            
            chapter_audio = ChapterAudio.objects.filter(
                book_id=book_id,
                chapter_number=chapter_number,
                language=language,
                is_available=True
            ).first()
            
            if chapter_audio:
                # Also get next/previous chapter audio
                next_audio = ChapterAudio.objects.filter(
                    book_id=book_id,
                    chapter_number=chapter_number + 1,
                    language=language,
                    is_available=True
                ).first()
                
                prev_audio = ChapterAudio.objects.filter(
                    book_id=book_id,
                    chapter_number=chapter_number - 1,
                    language=language,
                    is_available=True
                ).first()
                
                return {
                    'success': True,
                    'has_audio': True,
                    'audio_url': chapter_audio.get_audio_url(),
                    'duration': chapter_audio.duration,
                    'chapter_number': chapter_number,
                    'next_chapter_audio': next_audio.chapter_number if next_audio else None,
                    'prev_chapter_audio': prev_audio.chapter_number if prev_audio else None,
                    'start_time': chapter_audio.start_time
                }
            
            return {'success': False, 'has_audio': False, 'message': 'No audio available for this chapter'}
            
        except Language.DoesNotExist:
            return {'success': False, 'error': f'Language {language_code} not found'}
    
    def get_user_audio_progress(self, user_id: int, book_id: int) -> Dict:
        """Get user's audio progress for a specific book"""
        try:
            progress = UserBookProgress.objects.get(
                user_id=user_id,
                book_id=book_id
            )
            
            book = Book.objects.get(id=book_id)
            
            return {
                'success': True,
                'current_chapter': progress.current_chapter,
                'current_verse': progress.current_verse,
                'audio_current_position': progress.audio_current_position,
                'audio_completed_chapters': progress.audio_completed_chapters,
                'completed': progress.completed,
                'progress_percentage': progress.get_audio_progress_percentage()
            }
        except UserBookProgress.DoesNotExist:
            return {
                'success': True,
                'current_chapter': 1,
                'current_verse': 1,
                'audio_current_position': 0,
                'audio_completed_chapters': [],
                'completed': False,
                'progress_percentage': 0
            }

    # ==================== AUDIO PROGRESS METHODS ====================

    def record_chapter_completion(self, user_id, book_id, chapter_number, language_code='en'):
        """Record that a user completed a chapter audio"""
        try:
            user = User.objects.get(id=user_id)
            book = Book.objects.get(id=book_id)
            language = Language.objects.get(code=language_code)

            progress, created = UserBookProgress.objects.get_or_create(
                user=user,
                book=book,
                defaults={
                    'current_chapter': chapter_number + 1 if chapter_number < book.total_chapters else chapter_number,
                    'current_verse': 1
                }
            )

            if not progress.audio_completed_chapters:
                progress.audio_completed_chapters = []

            if chapter_number not in progress.audio_completed_chapters:
                progress.audio_completed_chapters.append(chapter_number)
                progress.audio_completed_chapters.sort()

                # Update current chapter to next uncompleted chapter
                next_chapter = chapter_number + 1
                if next_chapter <= book.total_chapters:
                    progress.current_chapter = next_chapter

                progress.last_audio_listened = timezone.now()
                progress.save()

                # Check if book is complete
                if len(progress.audio_completed_chapters) >= book.total_chapters:
                    progress.completed = True
                    progress.save()

            pct = 0
            if book.total_chapters and book.total_chapters > 0:
                pct = (len(progress.audio_completed_chapters) / book.total_chapters) * 100

            return {
                'success': True,
                'completed_chapters': progress.audio_completed_chapters,
                'current_chapter': progress.current_chapter,
                'next_chapter': chapter_number + 1 if chapter_number < book.total_chapters else None,
                'book_completed': progress.completed,
                'progress_percentage': pct
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user_audio_status(self, user_id, book_id):
        """Get user's audio progress for a book"""
        try:
            progress = UserBookProgress.objects.get(user_id=user_id, book_id=book_id)
            pct = 0
            if progress.book.total_chapters and progress.book.total_chapters > 0:
                pct = (len(progress.audio_completed_chapters) / progress.book.total_chapters) * 100

            return {
                'success': True,
                'completed_chapters': progress.audio_completed_chapters,
                'current_chapter': progress.current_chapter,
                'book_completed': progress.completed,
                'progress_percentage': pct
            }
        except UserBookProgress.DoesNotExist:
            return {
                'success': True,
                'completed_chapters': [],
                'current_chapter': 1,
                'book_completed': False,
                'progress_percentage': 0
            }
    
    def update_audio_progress(self, user_id: int, book_id: int, chapter_number: int, 
                              current_position: int = None, completed_chapter: int = None) -> Dict:
        """Update user's audio progress for a book"""
        try:
            progress, created = UserBookProgress.objects.get_or_create(
                user_id=user_id,
                book_id=book_id,
                defaults={
                    'current_chapter': chapter_number,
                    'current_verse': 1
                }
            )
            
            # Update current chapter
            progress.current_chapter = chapter_number
            
            # Update audio position if provided
            if current_position is not None:
                progress.audio_current_position = current_position
                progress.last_audio_listened = timezone.now()
            
            # Mark chapter as completed if provided
            if completed_chapter is not None:
                if not progress.audio_completed_chapters:
                    progress.audio_completed_chapters = []
                if completed_chapter not in progress.audio_completed_chapters:
                    progress.audio_completed_chapters.append(completed_chapter)
                    progress.audio_completed_chapters.sort()
            
            # Check if book is fully completed
            book = Book.objects.get(id=book_id)
            if len(progress.audio_completed_chapters) >= book.total_chapters:
                progress.completed = True
            
            progress.save()
            
            return {
                'success': True,
                'current_chapter': progress.current_chapter,
                'audio_current_position': progress.audio_current_position,
                'audio_completed_chapters': progress.audio_completed_chapters,
                'completed': progress.completed,
                'progress_percentage': progress.get_audio_progress_percentage()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== BOOK CONTENT METHODS ====================
    
    def get_book_full_content(self, book_name: str, language_code: str = 'en') -> Dict:
        """Get full content of a specific book with book info and chapter audio"""
        try:
            book_name = unquote(book_name)
            language = Language.objects.get(code=language_code)
            
            # Get book info
            book = Book.objects.filter(
                Q(name__iexact=book_name) | 
                Q(name__icontains=book_name)
            ).first()
            
            if not book:
                return {'error': f'Book "{book_name}" not found'}
            
            # Get all chapter audio availability at once
            chapter_audios = ChapterAudio.objects.filter(
                book=book,
                language=language,
                is_available=True
            ).values('chapter_number', 'audio_url', 'duration')
            
            # Create a lookup dict for chapter audio
            audio_lookup = {}
            for ca in chapter_audios:
                audio_lookup[ca['chapter_number']] = {
                    'has_audio': True,
                    'audio_url': ca['audio_url'],
                    'audio_duration': ca['duration']
                }
            
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
            chapters_content = []
            current_chapter = None
            current_verses = []
            
            for verse in verses:
                chapter = verse['verse__chapter__chapter_number']
                
                if current_chapter != chapter:
                    if current_chapter is not None:
                        audio_info_chapter = audio_lookup.get(current_chapter, {
                            'has_audio': False,
                            'audio_url': None,
                            'audio_duration': None
                        })
                        chapters_content.append({
                            'chapter': current_chapter,
                            'has_audio': audio_info_chapter['has_audio'],
                            'audio_url': audio_info_chapter['audio_url'],
                            'audio_duration': audio_info_chapter['audio_duration'],
                            'verses': current_verses
                        })
                    current_chapter = chapter
                    current_verses = []
                
                current_verses.append({
                    'verse': verse['verse__verse_number'],
                    'text': verse['text']
                })
            
            # Add last chapter
            if current_chapter is not None:
                audio_info_chapter = audio_lookup.get(current_chapter, {
                    'has_audio': False,
                    'audio_url': None,
                    'audio_duration': None
                })
                chapters_content.append({
                    'chapter': current_chapter,
                    'has_audio': audio_info_chapter['has_audio'],
                    'audio_url': audio_info_chapter['audio_url'],
                    'audio_duration': audio_info_chapter['audio_duration'],
                    'verses': current_verses
                })
            
            # Get overall book audio info
            book_audio = BookAudio.objects.filter(
                book=book,
                language=language,
                is_available=True
            ).first()
            
            # Check if any chapter has audio
            has_any_audio = len(audio_lookup) > 0 or book_audio is not None
            
            audio_info = {
                'has_audio': has_any_audio,
                'type': 'full_book' if book_audio else ('chapter_by_chapter' if len(audio_lookup) > 0 else 'none'),
                'book_audio_url': book_audio.get_audio_url() if book_audio else None,
                'book_duration': book_audio.duration if book_audio else None,
                'chapters_with_audio': len(audio_lookup)
            }
            
            return {
                'book_info': {
                    'id': book.id,
                    'name': book.name,
                    'testament': book.testament.name if book.testament else None,
                    'total_chapters': book.chapters.count(),
                    'total_verses': Verse.objects.filter(chapter__book=book).count(),
                    'has_audio': book.has_audio or has_any_audio
                },
                'audio_info': audio_info,
                'chapters': chapters_content
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
                'book_id': book.id,
                'total_chapters': chapters.count(),
                'has_audio': book.has_audio,
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
                'has_audio': book.has_audio,
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
            
            # Get audio for this chapter
            audio_info = self.get_chapter_audio(book.id, chapter, language_code)
            
            return {
                'reference': f'{book.name} {chapter}',
                'book': book.name,
                'book_id': book.id,
                'chapter': chapter,
                'total_verses': verses.count(),
                'has_audio': audio_info.get('has_audio', False),
                'audio_url': audio_info.get('audio_url') if audio_info.get('has_audio') else None,
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
                    'book_id': book.id,
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
            'verse__chapter__book__id',
            'verse__chapter__chapter_number',
            'verse__verse_number',
            'text'
        )[:limit]
        
        return [
            {
                'reference': f"{vt['verse__chapter__book__name']} {vt['verse__chapter__chapter_number']}:{vt['verse__verse_number']}",
                'book': vt['verse__chapter__book__name'],
                'book_id': vt['verse__chapter__book__id'],
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
            'book_id': verse_text.verse.chapter.book.id,
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
            'book_id': verse_text.verse.chapter.book.id,
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
    
    def get_audio_stats(self) -> Dict:
        """Get statistics about audio availability"""
        total_books = Book.objects.count()
        books_with_audio = Book.objects.filter(has_audio=True).count()
        
        total_chapter_audio = ChapterAudio.objects.filter(is_available=True).count()
        total_book_audio = BookAudio.objects.filter(is_available=True).count()
        
        return {
            'total_books': total_books,
            'books_with_audio': books_with_audio,
            'books_without_audio': total_books - books_with_audio,
            'chapter_audio_files': total_chapter_audio,
            'book_audio_files': total_book_audio,
            'audio_coverage_percentage': (books_with_audio / total_books * 100) if total_books > 0 else 0
        }