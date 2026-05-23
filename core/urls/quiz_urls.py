"""
Quiz URLs - Quiz management endpoints
"""

from django.urls import path
from ..views.quiz import (
    BookLevelsView,
    StartQuizView,
    NextQuestionView,
    SubmitAnswerView,
    FinishQuizView,
    QuizReviewView
)

urlpatterns = [
    # Book levels
    path('books/<int:book_id>/levels', BookLevelsView.as_view(), name='quiz-book-levels'),
    
    # Quiz flow
    path('start', StartQuizView.as_view(), name='quiz-start'),
    path('answer', SubmitAnswerView.as_view(), name='quiz-answer'),
    path('<int:attempt_id>/next', NextQuestionView.as_view(), name='quiz-next'),
    path('<int:attempt_id>/finish', FinishQuizView.as_view(), name='quiz-finish'),
    path('<int:attempt_id>/review', QuizReviewView.as_view(), name='quiz-review'),
]