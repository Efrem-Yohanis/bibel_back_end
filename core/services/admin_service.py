"""
Admin Service - Comprehensive admin management for books, languages, users, imports
"""

from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from typing import List, Dict, Optional, Any
import json
import re
from pathlib import Path

from ..models import (
    Language, Book, Testament, Chapter, Verse, VerseText,
    Question, QuestionText, Option, OptionText, Explanation,
    User, QuizAttempt, UserBookProgress, Level
)


class AdminBookService:
    """Admin book management service"""
    
    def get_all_books(self, testament: str = None) -> List[Dict]:
        """Get all books, optionally filtered by testament"""
        queryset = Book.objects.select_related('testament').annotate(
            chapters_count=models.Count('chapters__id', distinct=True),
            verses_count=models.Count('chapters__verses__id', distinct=True)
        )
        
        if testament:
            queryset = queryset.filter(testament__name=testament)
        
        books = []
        for book in queryset.order_by('id'):
            books.append({
                'id': book.id,
                'name': book.name,
                'testament': book.testament.name if book.testament else None,
                'chapters': book.chapters_count,
                'verses': book.verses_count
            })
        
        return books
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict]:
        """Get book by ID"""
        try:
            book = Book.objects.select_related('testament').annotate(
                chapters_count=models.Count('chapters__id', distinct=True),
                verses_count=models.Count('chapters__verses__id', distinct=True)
            ).get(id=book_id)
            
            return {
                'id': book.id,
                'name': book.name,
                'testament': book.testament.name if book.testament else None,
                'chapters': book.chapters_count,
                'verses': book.verses_count
            }
        except Book.DoesNotExist:
            return None
    
    def add_book(self, name: str, testament_name: str) -> Dict:
        """Add a new book"""
        try:
            testament = Testament.objects.get(name=testament_name)
            
            if Book.objects.filter(name=name).exists():
                return {'success': False, 'message': f'Book "{name}" already exists'}
            
            book = Book.objects.create(name=name, testament=testament)
            
            return {
                'success': True,
                'book_id': book.id,
                'message': 'Book added successfully'
            }
        except Testament.DoesNotExist:
            return {'success': False, 'message': f'Testament "{testament_name}" not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def update_book(self, book_id: int, name: str = None, testament_name: str = None) -> Dict:
        """Update book information"""
        try:
            book = Book.objects.get(id=book_id)
            
            if name:
                book.name = name
            
            if testament_name:
                testament = Testament.objects.get(name=testament_name)
                book.testament = testament
            
            book.save()
            
            return {'success': True, 'message': 'Book updated successfully'}
        except Book.DoesNotExist:
            return {'success': False, 'message': 'Book not found'}
        except Testament.DoesNotExist:
            return {'success': False, 'message': f'Testament "{testament_name}" not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def delete_book(self, book_id: int) -> Dict:
        """Delete a book (cascade will handle related records)"""
        try:
            book = Book.objects.get(id=book_id)
            
            # Check if book has questions
            question_count = Question.objects.filter(book=book).count()
            if question_count > 0:
                return {
                    'success': False,
                    'message': f'Cannot delete: Book has {question_count} questions'
                }
            
            book.delete()
            return {'success': True, 'message': 'Book deleted successfully'}
        except Book.DoesNotExist:
            return {'success': False, 'message': 'Book not found'}


class AdminLanguageService:
    """Admin language management service"""
    
    def get_all_languages(self) -> List[Dict]:
        """Get all languages"""
        languages = Language.objects.all().values(
            'id', 'code', 'name', 'native_name', 'is_active', 'created_at'
        ).order_by('id')
        
        return list(languages)
    
    def add_language(self, code: str, name: str, native_name: str = None) -> Dict:
        """Add a new language"""
        try:
            if Language.objects.filter(code=code).exists():
                return {'success': False, 'message': f'Language with code "{code}" already exists'}
            
            language = Language.objects.create(
                code=code,
                name=name,
                native_name=native_name or '',
                is_active=True,
                created_at=timezone.now()
            )
            
            return {
                'success': True,
                'language_id': language.id,
                'message': 'Language added successfully'
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def update_language(self, language_id: int, **kwargs) -> Dict:
        """Update language information"""
        try:
            language = Language.objects.get(id=language_id)
            
            if 'code' in kwargs:
                language.code = kwargs['code']
            if 'name' in kwargs:
                language.name = kwargs['name']
            if 'native_name' in kwargs:
                language.native_name = kwargs['native_name']
            if 'is_active' in kwargs:
                language.is_active = kwargs['is_active']
            
            language.save()
            
            return {'success': True, 'message': 'Language updated successfully'}
        except Language.DoesNotExist:
            return {'success': False, 'message': 'Language not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def delete_language(self, language_id: int) -> Dict:
        """Delete a language (only if no references exist)"""
        try:
            language = Language.objects.get(id=language_id)
            
            # Check if language is used
            verse_count = VerseText.objects.filter(language=language).count()
            if verse_count > 0:
                return {
                    'success': False,
                    'message': f'Cannot delete: Language is used in {verse_count} verses'
                }
            
            question_count = QuestionText.objects.filter(language=language).count()
            if question_count > 0:
                return {
                    'success': False,
                    'message': f'Cannot delete: Language is used in {question_count} questions'
                }
            
            language.delete()
            return {'success': True, 'message': 'Language deleted successfully'}
        except Language.DoesNotExist:
            return {'success': False, 'message': 'Language not found'}


class AdminUserService:
    """Admin user management service"""
    
    def get_all_users(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all registered users"""
        users = User.objects.all().values(
            'id', 'username', 'email', 'created_at', 'last_login',
            'is_active', 'is_admin', 'total_quizzes_taken',
            'total_correct_answers', 'total_questions_answered'
        ).order_by('-id')[offset:offset + limit]
        
        return list(users)
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            user = User.objects.get(id=user_id)
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'total_quizzes_taken': user.total_quizzes_taken,
                'total_correct_answers': user.total_correct_answers,
                'total_questions_answered': user.total_questions_answered
            }
        except User.DoesNotExist:
            return None
    
    def get_user_quiz_progress(self, user_id: int) -> Dict:
        """Get user's quiz progress"""
        # Get quiz attempts
        attempts = QuizAttempt.objects.filter(user_id=user_id).select_related(
            'book', 'level'
        ).values(
            'id', 'book__name', 'level__name', 'total_questions',
            'correct_answers', 'score_percentage', 'status',
            'started_at', 'completed_at'
        ).order_by('-started_at')
        
        # Get book progress
        book_progress = UserBookProgress.objects.filter(user_id=user_id).select_related(
            'book'
        ).values(
            'book__name', 'current_chapter', 'current_verse',
            'questions_answered', 'correct_answers', 'completed', 'last_activity'
        ).order_by('book__name')
        
        return {
            'quiz_attempts': list(attempts),
            'book_progress': list(book_progress),
            'total_quizzes': attempts.count(),
            'total_books_progress': book_progress.count()
        }
    
    def toggle_user_status(self, user_id: int, is_active: bool) -> bool:
        """Activate or deactivate user"""
        try:
            user = User.objects.get(id=user_id)
            user.is_active = is_active
            user.updated_at = timezone.now()
            user.save()
            return True
        except User.DoesNotExist:
            return False
    
    def set_user_admin_status(self, user_id: int, is_admin: bool) -> bool:
        """Promote or demote a user to/from admin"""
        try:
            user = User.objects.get(id=user_id)
            user.is_admin = is_admin
            user.updated_at = timezone.now()
            user.save()
            return True
        except User.DoesNotExist:
            return False
    
    def get_user_count(self) -> int:
        """Get total number of users"""
        return User.objects.count()
    
    def get_user_stats_summary(self) -> Dict:
        """Get summary statistics for all users"""
        from django.db.models import Sum, Avg
        
        stats = User.objects.aggregate(
            total_users=models.Count('id'),
            total_quizzes=Sum('total_quizzes_taken'),
            total_questions=Sum('total_questions_answered'),
            total_correct=Sum('total_correct_answers'),
            avg_quizzes_per_user=Avg('total_quizzes_taken')
        )
        
        return {
            'total_users': stats['total_users'] or 0,
            'total_quizzes': stats['total_quizzes'] or 0,
            'total_questions': stats['total_questions'] or 0,
            'total_correct': stats['total_correct'] or 0,
            'avg_quizzes_per_user': round(stats['avg_quizzes_per_user'] or 0, 2)
        }


class AdminBibleImportService:
    """Service for importing Bible texts"""
    
    def __init__(self):
        self.imported_count = 0
    
    def _get_or_create_testament(self, book_name: str) -> Testament:
        """Get or create testament based on book name"""
        nt_books = [
            'Matthew', 'Mark', 'Luke', 'John', 'Acts',
            'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
            'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians',
            '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
            'James', '1 Peter', '2 Peter', '1 John', '2 John', '3 John', 'Jude', 'Revelation'
        ]
        
        testament_name = 'New' if book_name in nt_books else 'Old'
        testament, _ = Testament.objects.get_or_create(name=testament_name)
        return testament
    
    def _parse_bible_file(self, file_path: Path, language_code: str) -> List[Dict]:
        """Parse Bible text file"""
        verses = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        lines = content.split('\n')
        current_book = None
        current_chapter = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse book name
            if line.startswith('Book:'):
                match = re.search(r'Book:\s+(.+?)(?:\s+\(|$)', line)
                if match:
                    current_book = match.group(1).strip()
                continue
            
            # Parse chapter number
            if line.startswith('Chapter'):
                match = re.search(r'Chapter\s+(\d+)', line, re.IGNORECASE)
                if match:
                    current_chapter = int(match.group(1))
                continue
            
            # Skip separators
            if line.startswith('==') or line.startswith('--') or line.startswith('***'):
                continue
            
            # Parse verse
            verse_match = re.match(r'^(\d+)\s*[-:]\s*(.+)$', line)
            if verse_match and current_chapter and current_book:
                verse_num = int(verse_match.group(1))
                verse_text = verse_match.group(2).strip()
                
                verses.append({
                    'book_name': current_book,
                    'chapter': current_chapter,
                    'verse': verse_num,
                    'text': verse_text,
                    'language_code': language_code
                })
        
        return verses
    
    @transaction.atomic
    def import_book(self, file_path: str, language_code: str) -> Dict:
        """Import a single book"""
        try:
            file_path = Path(file_path)
            
            # Get language
            try:
                language = Language.objects.get(code=language_code)
            except Language.DoesNotExist:
                return {'success': False, 'message': f'Language "{language_code}" not found'}
            
            verses = self._parse_bible_file(file_path, language_code)
            
            if not verses:
                return {'success': False, 'message': 'No verses found in file'}
            
            book_name = verses[0]['book_name']
            
            # Get or create testament and book
            testament = self._get_or_create_testament(book_name)
            book, _ = Book.objects.get_or_create(name=book_name, testament=testament)
            
            verse_count = 0
            for verse_data in verses:
                # Get or create chapter
                chapter, _ = Chapter.objects.get_or_create(
                    book=book,
                    chapter_number=verse_data['chapter']
                )
                
                # Get or create verse
                verse, _ = Verse.objects.get_or_create(
                    chapter=chapter,
                    verse_number=verse_data['verse']
                )
                
                # Create or update verse text
                VerseText.objects.update_or_create(
                    verse=verse,
                    language=language,
                    defaults={'text': verse_data['text']}
                )
                verse_count += 1
            
            return {
                'success': True,
                'message': f'Successfully imported {book_name}',
                'book_name': book_name,
                'verses_imported': verse_count,
                'language': language_code
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_import_status(self) -> Dict:
        """Get current import status"""
        books_count = Book.objects.count()
        verses_count = Verse.objects.count()
        
        verse_texts_by_language = {}
        for lang in Language.objects.filter(is_active=True):
            count = VerseText.objects.filter(language=lang).count()
            if count > 0:
                verse_texts_by_language[lang.code] = count
        
        return {
            'books_imported': books_count,
            'verses_imported': verses_count,
            'verse_texts_by_language': verse_texts_by_language,
            'languages_available': list(verse_texts_by_language.keys())
        }


class AdminQuestionsImportService:
    """Service for importing quiz questions"""
    
    def __init__(self):
        self.imported_count = 0
    
    def _get_or_create_chapter(self, book_id: int, chapter_number: int) -> Chapter:
        """Get or create chapter"""
        chapter, _ = Chapter.objects.get_or_create(
            book_id=book_id,
            chapter_number=chapter_number
        )
        return chapter
    
    @transaction.atomic
    def import_questions_json(self, json_file_path: str, language_code: str) -> Dict:
        """Import questions from JSON file"""
        try:
            # Get language
            try:
                language = Language.objects.get(code=language_code)
            except Language.DoesNotExist:
                return {'success': False, 'message': f'Language "{language_code}" not found'}
            
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            book_name = Path(json_file_path).stem.replace('questions_', '')
            
            # Get book
            try:
                book = Book.objects.get(name__icontains=book_name)
            except Book.DoesNotExist:
                return {'success': False, 'message': f'Book "{book_name}" not found in database'}
            
            questions_imported = 0
            
            for q in data.get('questions', []):
                # Parse chapter number from verse reference
                chapter_number = 1
                vr = q.get('verse_reference', '')
                match = re.search(r"(\d+):", vr)
                if match:
                    chapter_number = int(match.group(1))
                
                # Get or create chapter
                chapter = self._get_or_create_chapter(book.id, chapter_number)
                
                # Get level
                level_num = q.get('level', 1)
                try:
                    level_num = int(level_num)
                except:
                    level_num = 1
                
                level = Level.objects.filter(level_number=level_num).first()
                if not level:
                    level = Level.objects.filter(level_number=1).first()
                
                correct_option = q.get('correct_answer') or q.get('correct_option') or 'A'
                
                # Create question
                question = Question.objects.create(
                    book=book,
                    chapter=chapter,
                    level=level,
                    correct_option=correct_option,
                    verse_reference=vr
                )
                
                # Create question text
                QuestionText.objects.create(
                    question=question,
                    language=language,
                    text=q.get('question', '')
                )
                
                # Handle options
                options_data = q.get('options', {})
                if isinstance(options_data, dict):
                    items = list(options_data.items())
                elif isinstance(options_data, list):
                    items = []
                    for opt in options_data:
                        if isinstance(opt, dict):
                            label = opt.get('label') or opt.get('option')
                            text = opt.get('text') or opt.get('value')
                            items.append((label, text))
                else:
                    items = []
                
                for label, text in items:
                    if not label:
                        continue
                    label_str = str(label).strip()
                    option = Option.objects.create(
                        question=question,
                        label=label_str
                    )
                    OptionText.objects.create(
                        option=option,
                        language=language,
                        text=text
                    )
                
                # Create explanation
                if q.get('explanation'):
                    Explanation.objects.create(
                        question=question,
                        language=language,
                        text=q.get('explanation', '')
                    )
                
                questions_imported += 1
            
            return {
                'success': True,
                'message': f'Successfully imported {questions_imported} questions for {book_name}',
                'book_name': book_name,
                'questions_imported': questions_imported,
                'language': language_code
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def get_questions_status(self) -> Dict:
        """Get current questions import status"""
        questions_count = Question.objects.count()
        
        questions_by_language = {}
        for lang in Language.objects.filter(is_active=True):
            count = QuestionText.objects.filter(language=lang).count()
            if count > 0:
                questions_by_language[lang.code] = count
        
        return {
            'total_questions': questions_count,
            'questions_by_language': questions_by_language
        }