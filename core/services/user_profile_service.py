"""
User Profile Service - Manages user quiz history, progress, and resume functionality
"""

from django.db import models
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from typing import Dict, List, Optional, Any
import json
from ..models import User, QuizAttempt, QuizAnswer, UserBookProgress, Book, Testament


class UserProfileService:
    """Service for managing user profiles, quiz history, and progress"""
    
    def __init__(self):
        pass
    
    def get_user_complete_profile(self, user_id: int) -> Dict[str, Any]:
        """Get complete user profile with all history and progress"""
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return {'error': 'User not found'}
        
        # Calculate accuracy
        accuracy = 0
        if user.total_questions_answered > 0:
            accuracy = (user.total_correct_answers / user.total_questions_answered) * 100
        
        # Get data
        quiz_history = self.get_quiz_history(user_id)
        in_progress_quizzes = self.get_in_progress_quizzes(user_id)
        book_progress = self.get_book_progress(user_id)
        recent_activity = self.get_recent_activity(user_id)
        
        return {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'member_since': user.created_at,
                'last_login': user.last_login,
                'is_active': user.is_active
            },
            'statistics': {
                'total_quizzes_taken': user.total_quizzes_taken or 0,
                'total_questions_answered': user.total_questions_answered or 0,
                'total_correct_answers': user.total_correct_answers or 0,
                'accuracy_percentage': round(accuracy, 2)
            },
            'quiz_history': quiz_history,
            'in_progress_quizzes': in_progress_quizzes,
            'book_progress': book_progress,
            'recent_activity': recent_activity,
            'can_resume': len(in_progress_quizzes) > 0
        }
    
    def get_quiz_history(self, user_id: int) -> List[Dict]:
        """Get user's quiz history"""
        attempts = QuizAttempt.objects.filter(
            user_id=user_id,
            status='completed'
        ).select_related('book', 'level', 'language').order_by('-completed_at')[:50]
        
        history = []
        for attempt in attempts:
            history.append({
                'id': attempt.id,
                'book_name': attempt.book.name if attempt.book else None,
                'testament': attempt.book.testament.name if attempt.book and attempt.book.testament else None,
                'total_questions': attempt.total_questions,
                'answered_questions': attempt.total_questions,
                'correct_answers': attempt.correct_answers,
                'score_percentage': attempt.score_percentage,
                'status': attempt.status,
                'started_at': attempt.started_at,
                'completed_at': attempt.completed_at
            })
        
        return history
    
    def get_in_progress_quizzes(self, user_id: int) -> List[Dict]:
        """Get quizzes that are in progress (can be resumed)"""
        attempts = QuizAttempt.objects.filter(
            user_id=user_id,
            status='in_progress'
        ).select_related('book', 'level', 'language').order_by('-started_at')
        
        quizzes = []
        for attempt in attempts:
            quiz = {
                'id': attempt.id,
                'book_name': attempt.book.name if attempt.book else None,
                'testament': attempt.book.testament.name if attempt.book and attempt.book.testament else None,
                'total_questions': attempt.total_questions,
                'answered_questions': 0,
                'correct_answers': attempt.correct_answers,
                'score_percentage': attempt.score_percentage,
                'started_at': attempt.started_at,
                'resume_data': attempt.resume_data
            }
            
            # Parse resume data if exists
            if quiz.get('resume_data'):
                try:
                    quiz['resume_data'] = json.loads(quiz['resume_data'])
                    quiz['answered_questions'] = quiz['resume_data'].get('current_index', 0)
                except:
                    quiz['resume_data'] = None
            
            quizzes.append(quiz)
        
        return quizzes
    
    def get_book_progress(self, user_id: int) -> List[Dict]:
        """Get user's progress through each book"""
        progress_records = UserBookProgress.objects.filter(
            user_id=user_id
        ).select_related('book').order_by('book__testament__name', 'book__name')
        
        progress = []
        for record in progress_records:
            progress.append({
                'book_name': record.book.name,
                'testament': record.book.testament.name if record.book.testament else None,
                'current_chapter': record.current_chapter,
                'current_verse': record.current_verse,
                'questions_answered': record.questions_answered,
                'correct_answers': record.correct_answers,
                'last_activity': record.last_activity,
                'completed': record.completed
            })
        
        return progress
    
    def get_recent_activity(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get recent user activity"""
        activities = []
        
        # Get recent quiz completions
        completed_quizzes = QuizAttempt.objects.filter(
            user_id=user_id,
            status='completed'
        ).select_related('book').order_by('-completed_at')[:limit]
        
        for quiz in completed_quizzes:
            activities.append({
                'activity_type': 'quiz_completed',
                'book_name': quiz.book.name if quiz.book else None,
                'score_percentage': quiz.score_percentage,
                'activity_date': quiz.completed_at
            })
        
        return activities
    
    def start_new_quiz(self, user_id: int, book_id: int, level_id: int = None, 
                      language_id: int = None, total_questions: int = 10) -> Dict:
        """Start a new quiz session"""
        try:
            attempt = QuizAttempt.objects.create(
                user_id=user_id,
                book_id=book_id,
                level_id=level_id,
                language_id=language_id,
                total_questions=total_questions,
                correct_answers=0,
                score_percentage=0,
                status='in_progress',
                started_at=timezone.now(),
                resume_data=None
            )
            
            book = Book.objects.get(id=book_id)
            
            return {
                'attempt_id': attempt.id,
                'book_name': book.name,
                'testament': book.testament.name if book.testament else None,
                'total_questions': total_questions,
                'status': 'in_progress',
                'started_at': attempt.started_at.isoformat()
            }
            
        except Exception as e:
            return {'error': f'Failed to start quiz: {str(e)}'}
    
    def save_quiz_answer(self, attempt_id: int, question_data: Dict) -> bool:
        """Save an answer for a quiz"""
        try:
            QuizAnswer.objects.create(
                attempt_id=attempt_id,
                question_id=question_data.get('question_id'),
                selected_option=question_data.get('selected_option'),
                is_correct=question_data.get('is_correct', False),
                answered_at=timezone.now()
            )
            
            # Update attempt statistics
            attempt = QuizAttempt.objects.get(id=attempt_id)
            
            if question_data.get('is_correct'):
                attempt.correct_answers += 1
            
            if attempt.total_questions > 0:
                attempt.score_percentage = (attempt.correct_answers / attempt.total_questions) * 100
            
            attempt.save()
            
            return True
            
        except Exception as e:
            print(f"Error saving answer: {e}")
            return False
    
    def complete_quiz(self, attempt_id: int) -> Dict:
        """Mark a quiz as completed and update user stats"""
        try:
            attempt = QuizAttempt.objects.get(id=attempt_id)
            
            if attempt.status == 'completed':
                return {'error': 'Quiz already completed'}
            
            # Mark as completed
            attempt.status = 'completed'
            attempt.completed_at = timezone.now()
            attempt.save()
            
            # Update user statistics
            user = attempt.user
            user.total_quizzes_taken += 1
            user.total_questions_answered += attempt.total_questions
            user.total_correct_answers += attempt.correct_answers
            user.updated_at = timezone.now()
            user.save()
            
            return {
                'success': True,
                'score_percentage': attempt.score_percentage,
                'correct_answers': attempt.correct_answers,
                'total_questions': attempt.total_questions
            }
            
        except QuizAttempt.DoesNotExist:
            return {'error': 'Attempt not found'}
        except Exception as e:
            return {'error': f'Failed to complete quiz: {str(e)}'}
    
    def resume_quiz(self, attempt_id: int) -> Dict:
        """Get quiz data to resume from where user stopped"""
        try:
            attempt = QuizAttempt.objects.get(id=attempt_id, status='in_progress')
        except QuizAttempt.DoesNotExist:
            return {'error': 'No in-progress quiz found to resume'}
        
        # Get previous answers
        previous_answers = QuizAnswer.objects.filter(
            attempt_id=attempt_id
        ).values('question_id', 'selected_option', 'is_correct').order_by('answered_at')
        
        # Calculate progress
        answered_count = previous_answers.count()
        progress_percentage = (answered_count / attempt.total_questions) * 100 if attempt.total_questions > 0 else 0
        
        result = {
            'attempt_id': attempt.id,
            'book_name': attempt.book.name if attempt.book else None,
            'testament': attempt.book.testament.name if attempt.book and attempt.book.testament else None,
            'total_questions': attempt.total_questions,
            'answered_questions': answered_count,
            'correct_answers': attempt.correct_answers,
            'score_percentage': attempt.score_percentage,
            'progress_percentage': progress_percentage,
            'previous_answers': list(previous_answers),
            'started_at': attempt.started_at,
            'can_resume': True
        }
        
        # Parse resume data if exists
        if attempt.resume_data:
            try:
                import json
                result['resume_data'] = json.loads(attempt.resume_data)
            except:
                pass
        
        return result
    
    def update_book_progress(self, user_id: int, book_id: int, 
                            chapter: int, verse: int) -> bool:
        """Update user's progress in a specific book"""
        try:
            progress, created = UserBookProgress.objects.update_or_create(
                user_id=user_id,
                book_id=book_id,
                defaults={
                    'current_chapter': chapter,
                    'current_verse': verse,
                    'last_activity': timezone.now()
                }
            )
            return True
            
        except Exception as e:
            print(f"Error updating book progress: {e}")
            return False
    
    def get_user_statistics(self, user_id: int) -> Dict:
        """Get aggregated user statistics"""
        try:
            user = User.objects.get(id=user_id)
            
            # Get quiz statistics
            quiz_stats = QuizAttempt.objects.filter(user_id=user_id, status='completed').aggregate(
                total_quizzes=Count('id'),
                avg_score=Avg('score_percentage'),
                best_score=models.Max('score_percentage')
            )
            
            # Get favorite book (most quizzes taken)
            favorite_book = QuizAttempt.objects.filter(
                user_id=user_id, 
                status='completed',
                book__isnull=False
            ).values('book__name').annotate(
                count=Count('id')
            ).order_by('-count').first()
            
            accuracy = 0
            if user.total_questions_answered > 0:
                accuracy = (user.total_correct_answers / user.total_questions_answered) * 100
            
            return {
                'total_quizzes': user.total_quizzes_taken,
                'total_questions': user.total_questions_answered,
                'total_correct': user.total_correct_answers,
                'accuracy': round(accuracy, 2),
                'average_score': round(quiz_stats['avg_score'] or 0, 2),
                'best_score': round(quiz_stats['best_score'] or 0, 2),
                'favorite_book': favorite_book['book__name'] if favorite_book else None,
                'books_started': UserBookProgress.objects.filter(user_id=user_id).count(),
                'books_completed': UserBookProgress.objects.filter(user_id=user_id, completed=True).count()
            }
            
        except User.DoesNotExist:
            return {'error': 'User not found'}