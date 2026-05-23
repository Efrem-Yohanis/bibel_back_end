"""
Quiz Service - Manages quiz with one-by-one question flow
"""

from django.db import models
from django.utils import timezone
from typing import List, Dict, Optional, Any
import json
import random
import re
from ..models import (
    User, Book, Level, Language, Question, QuestionText,
    Option, OptionText, Explanation, QuizAttempt, QuizAnswer, VerseText
)


class QuizService:
    """Service for quiz operations with one-by-one question flow"""
    
    def __init__(self):
        pass
    
    # ==================== Helper Methods ====================
    
    def get_language_id(self, language_code: str) -> Optional[int]:
        """Get language ID from code"""
        try:
            language = Language.objects.get(code=language_code)
            return language.id
        except Language.DoesNotExist:
            return None
    
    def get_level_id(self, level_number: int) -> Optional[int]:
        """Get level ID from level number"""
        try:
            level = Level.objects.get(level_number=level_number)
            return level.id
        except Level.DoesNotExist:
            return None
    
    def get_book_name(self, book_id: int) -> str:
        """Get book name by ID"""
        try:
            book = Book.objects.get(id=book_id)
            return book.name
        except Book.DoesNotExist:
            return 'Unknown'
    
    def get_book_levels(self, book_id: int) -> Dict:
        """Get available quiz levels for a specific book"""
        try:
            # Get unique levels for this book
            levels = Level.objects.filter(
                questions__book_id=book_id
            ).distinct().values(
                'id', 'level_number', 'name', 'description', 'icon', 'color'
            ).order_by('level_number')
            
            book_name = self.get_book_name(book_id)
            
            if not book_name:
                return {'error': 'Book not found'}
            
            return {
                'book_id': book_id,
                'book_name': book_name,
                'levels': list(levels)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    # ==================== Quiz Flow Methods ====================
    
    def start_quiz(self, user_id: int, book_id: int, level_id: int, language_id: int) -> Dict:
        """Start a new quiz session"""
        try:
            # Get all question IDs for this book and level
            questions = Question.objects.filter(
                book_id=book_id,
                level_id=level_id
            ).values_list('id', flat=True).order_by('id')
            
            question_ids = list(questions)
            
            if not question_ids:
                return {'error': 'No questions found for this book and level'}
            
            # Shuffle questions
            random.shuffle(question_ids)
            
            total_questions = len(question_ids)
            
            # Create resume data
            resume_data = {
                'question_ids': question_ids,
                'current_index': 0,
                'answers': [],
                'book_id': book_id,
                'level_id': level_id,
                'language_id': language_id
            }
            
            # Create quiz attempt
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
                resume_data=json.dumps(resume_data)
            )
            
            return {
                'attempt_id': attempt.id,
                'book_id': book_id,
                'level_id': level_id,
                'language_id': language_id,
                'total_questions': total_questions,
                'current_question_number': 1,
                'status': 'in_progress'
            }
            
        except Exception as e:
            return {'error': f'Failed to start quiz: {str(e)}'}
    
    def get_next_question(self, attempt_id: int, user_id: int) -> Dict:
        """Get the next question for the quiz"""
        try:
            # Get quiz attempt
            attempt = QuizAttempt.objects.get(id=attempt_id, user_id=user_id)
            
            if attempt.status != 'in_progress':
                return {'error': 'Quiz already completed'}
            
            # Parse resume data
            resume_data = json.loads(attempt.resume_data)
            question_ids = resume_data['question_ids']
            current_index = resume_data['current_index']
            language_id = resume_data.get('language_id')
            
            # Check if quiz is complete
            if current_index >= len(question_ids):
                return {'completed': True, 'message': 'Quiz completed'}
            
            # Get the next question
            question_id = question_ids[current_index]
            
            question_data = Question.objects.filter(id=question_id).first()
            if not question_data:
                return {'error': 'Question not found'}
            
            # Get question text
            question_text = QuestionText.objects.filter(
                question_id=question_id,
                language_id=language_id
            ).first()
            
            # Get options
            options = []
            option_objects = Option.objects.filter(question_id=question_id).order_by('label')
            
            for opt in option_objects:
                option_text = OptionText.objects.filter(
                    option_id=opt.id,
                    language_id=language_id
                ).first()
                options.append({
                    'label': opt.label,
                    'text': option_text.text if option_text else opt.label
                })
            
            return {
                'attempt_id': attempt_id,
                'question_number': current_index + 1,
                'remaining_questions': len(question_ids) - current_index - 1,
                'question': {
                    'question_id': question_id,
                    'text': question_text.text if question_text else '',
                    'verse_reference': question_data.verse_reference or '',
                    'options': options
                }
            }
            
        except QuizAttempt.DoesNotExist:
            return {'error': 'Quiz attempt not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def submit_answer(self, attempt_id: int, user_id: int, question_id: int, selected_option: str) -> Dict:
        """Submit an answer and move to next question"""
        try:
            # Get quiz attempt
            attempt = QuizAttempt.objects.get(id=attempt_id, user_id=user_id)
            
            if attempt.status != 'in_progress':
                return {'error': 'Quiz already completed'}
            
            # Parse resume data
            resume_data = json.loads(attempt.resume_data)
            question_ids = resume_data['question_ids']
            current_index = resume_data['current_index']
            language_id = resume_data.get('language_id')
            
            # Verify this is the expected question
            expected_question_id = question_ids[current_index]
            if expected_question_id != question_id:
                return {'error': 'Question out of order'}
            
            # Get question details
            question = Question.objects.filter(id=question_id).first()
            if not question:
                return {'error': 'Question not found'}
            
            # Check if answer is correct
            is_correct = (selected_option == question.correct_option)
            
            # Get correct option text
            correct_option_obj = Option.objects.filter(
                question_id=question_id,
                label=question.correct_option
            ).first()
            
            correct_text = ''
            if correct_option_obj:
                correct_option_text = OptionText.objects.filter(
                    option_id=correct_option_obj.id,
                    language_id=language_id
                ).first()
                correct_text = correct_option_text.text if correct_option_text else question.correct_option
            
            # Get explanation
            explanation_obj = Explanation.objects.filter(
                question_id=question_id,
                language_id=language_id
            ).first()
            explanation = explanation_obj.text if explanation_obj else ''
            
            # Get verse text
            verse_text = self._get_verse_text(question.verse_reference, language_id)
            
            # Save answer
            QuizAnswer.objects.create(
                attempt_id=attempt_id,
                question_id=question_id,
                selected_option=selected_option,
                is_correct=is_correct,
                answered_at=timezone.now()
            )
            
            # Update resume data
            resume_data['current_index'] = current_index + 1
            resume_data['answers'].append({
                'question_id': question_id,
                'selected_option': selected_option,
                'is_correct': is_correct
            })
            
            # Update attempt
            new_answered = current_index + 1
            correct_count = sum(1 for a in resume_data['answers'] if a['is_correct'])
            
            attempt.correct_answers = correct_count
            if attempt.total_questions > 0:
                attempt.score_percentage = (correct_count / attempt.total_questions) * 100
            attempt.resume_data = json.dumps(resume_data)
            attempt.save()
            
            # Check if quiz is complete
            is_complete = (new_answered >= attempt.total_questions)
            next_available = not is_complete
            
            result = {
                'is_correct': is_correct,
                'selected_option': selected_option,
                'correct_option': {
                    'label': question.correct_option,
                    'text': correct_text
                },
                'verse_reference': question.verse_reference or '',
                'explanation': explanation,
                'verse_text': verse_text,
                'progress': {
                    'current': new_answered,
                    'total': attempt.total_questions,
                    'remaining': attempt.total_questions - new_answered,
                    'percentage': round((new_answered / attempt.total_questions) * 100, 1) if attempt.total_questions > 0 else 0
                },
                'next_available': next_available
            }
            
            return result
            
        except QuizAttempt.DoesNotExist:
            return {'error': 'Quiz attempt not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def finish_quiz(self, attempt_id: int, user_id: int) -> Dict:
        """Finish the quiz and calculate final score"""
        try:
            # Get quiz attempt
            attempt = QuizAttempt.objects.get(id=attempt_id, user_id=user_id)
            
            if attempt.status == 'completed':
                return {'error': 'Quiz already completed'}
            
            # Parse resume data to get final stats
            resume_data = json.loads(attempt.resume_data) if attempt.resume_data else {}
            answers = resume_data.get('answers', [])
            correct_answers = sum(1 for a in answers if a.get('is_correct', False))
            
            # Ensure correct_answers is up to date
            if attempt.correct_answers != correct_answers:
                attempt.correct_answers = correct_answers
                if attempt.total_questions > 0:
                    attempt.score_percentage = (correct_answers / attempt.total_questions) * 100
            
            # Update attempt as completed
            attempt.status = 'completed'
            attempt.completed_at = timezone.now()
            attempt.save()
            
            # Update user statistics
            user = User.objects.get(id=user_id)
            user.total_quizzes_taken += 1
            user.total_questions_answered += attempt.total_questions
            user.total_correct_answers += attempt.correct_answers
            user.updated_at = timezone.now()
            user.save()
            
            total_questions = attempt.total_questions
            correct = attempt.correct_answers or 0
            wrong = total_questions - correct
            
            return {
                'attempt_id': attempt_id,
                'score_percentage': round(attempt.score_percentage, 2),
                'correct_answers': correct,
                'wrong_answers': wrong,
                'total_questions': total_questions,
                'status': 'completed'
            }
            
        except QuizAttempt.DoesNotExist:
            return {'error': 'Quiz attempt not found'}
        except User.DoesNotExist:
            return {'error': 'User not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_quiz_review(self, attempt_id: int, user_id: int) -> Dict:
        """Get full quiz review with all questions and answers"""
        try:
            # Get quiz attempt
            attempt = QuizAttempt.objects.get(id=attempt_id, user_id=user_id)
            
            # Get all answers
            answers_dict = {}
            for answer in QuizAnswer.objects.filter(attempt_id=attempt_id):
                answers_dict[answer.question_id] = answer
            
            # Get questions from resume_data
            resume_data = json.loads(attempt.resume_data) if attempt.resume_data else {}
            question_ids = resume_data.get('question_ids', [])
            language_id = resume_data.get('language_id', 1)
            
            # Build review data
            review_questions = []
            
            for qid in question_ids:
                question = Question.objects.filter(id=qid).first()
                if not question:
                    continue
                
                question_text = QuestionText.objects.filter(
                    question_id=qid,
                    language_id=language_id
                ).first()
                
                answer = answers_dict.get(qid)
                selected = answer.selected_option if answer else None
                is_correct = answer.is_correct if answer else False
                
                # Get explanation
                explanation_obj = Explanation.objects.filter(
                    question_id=qid,
                    language_id=language_id
                ).first()
                explanation = explanation_obj.text if explanation_obj else ""
                
                review_questions.append({
                    'question_id': qid,
                    'question': question_text.text if question_text else '',
                    'selected_option': selected,
                    'correct_option': question.correct_option,
                    'is_correct': is_correct,
                    'verse_reference': question.verse_reference or '',
                    'explanation': explanation
                })
            
            total_questions = attempt.total_questions
            correct_answers = attempt.correct_answers or 0
            wrong_answers = total_questions - correct_answers
            
            return {
                'attempt_id': attempt_id,
                'summary': {
                    'score_percentage': round(attempt.score_percentage or 0, 2),
                    'correct_answers': correct_answers,
                    'wrong_answers': wrong_answers,
                    'total_questions': total_questions
                },
                'questions': review_questions
            }
            
        except QuizAttempt.DoesNotExist:
            return {'error': 'Quiz attempt not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def _get_verse_text(self, reference: str, language_id: int) -> str:
        """Get verse text from reference using language ID"""
        if not reference:
            return ""
        
        # Parse reference like "John 3:16" or "Genesis 1:1"
        match = re.match(r'([\w\s]+)\s+(\d+):(\d+)', reference)
        if not match:
            return ""
        
        book_name = match.group(1).strip()
        chapter = int(match.group(2))
        verse = int(match.group(3))
        
        try:
            book = Book.objects.filter(name__icontains=book_name).first()
            if not book:
                return ""
            
            verse_text = VerseText.objects.filter(
                verse__chapter__book=book,
                verse__chapter__chapter_number=chapter,
                verse__verse_number=verse,
                language_id=language_id
            ).first()
            
            return verse_text.text if verse_text else ""
            
        except Exception:
            return ""