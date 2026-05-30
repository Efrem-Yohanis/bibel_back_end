"""
User Profile URLs - Profile management, password, quiz history, and progress
"""

from django.urls import path
from ..views.user import (
    # Profile management
    UserProfileView,
    ChangePasswordView,
    UserCompleteProfileView,
    
    # Statistics & History
    UserStatisticsView,
    QuizHistoryView,
    InProgressQuizzesView,
    
    # Quiz actions
    StartQuizView,
    SubmitAnswerView,
    CompleteQuizView,
    ResumeQuizView,
    
    # Reading progress
    BookProgressView,
    UpdateBookProgressView,
)

from ..views.bible import (
    UserAudioProgressView,
    UpdateAudioProgressView,
)

urlpatterns = [
    # ==================== PROFILE MANAGEMENT ====================
    # GET /api/user/profile - Get user profile
    # PUT /api/user/profile - Update user profile
    path('profile', UserProfileView.as_view(), name='user-profile'),
    
    # POST /api/user/change-password - Change user password
    path('change-password', ChangePasswordView.as_view(), name='user-change-password'),
    
    # ==================== STATISTICS & HISTORY ====================
    # GET /api/user/complete-profile - Complete profile with stats
    path('complete-profile', UserCompleteProfileView.as_view(), name='user-complete-profile'),
    
    # GET /api/user/statistics - Aggregated user statistics
    path('statistics', UserStatisticsView.as_view(), name='user-statistics'),
    
    # GET /api/user/quiz-history - User's quiz history
    path('quiz-history', QuizHistoryView.as_view(), name='user-quiz-history'),
    
    # GET /api/user/in-progress - In-progress quizzes
    path('in-progress', InProgressQuizzesView.as_view(), name='user-in-progress'),
    
    # ==================== QUIZ ACTIONS ====================
    # POST /api/user/quiz/start - Start a new quiz
    path('quiz/start', StartQuizView.as_view(), name='user-quiz-start'),
    
    # POST /api/user/quiz/submit-answer - Submit answer
    path('quiz/submit-answer', SubmitAnswerView.as_view(), name='user-quiz-submit-answer'),
    
    # POST /api/user/quiz/complete - Complete quiz
    path('quiz/complete', CompleteQuizView.as_view(), name='user-quiz-complete'),
    
    # GET /api/user/quiz/resume - Resume quiz
    path('quiz/resume', ResumeQuizView.as_view(), name='user-quiz-resume'),
    
    # ==================== READING PROGRESS ====================
    # GET /api/user/book-progress - Get book progress
    path('book-progress', BookProgressView.as_view(), name='user-book-progress'),
    
    # POST /api/user/update-progress - Update reading progress
    path('update-progress', UpdateBookProgressView.as_view(), name='user-update-progress'),

    # ==================== AUDIO PROGRESS ====================
    # GET /api/user/audio/progress/<book_id> - Get audio progress for a book
    path('audio/progress/<int:book_id>', UserAudioProgressView.as_view(), name='user-audio-progress'),
    # POST /api/user/audio/progress/<book_id>/update - Update audio progress for a book
    path('audio/progress/<int:book_id>/update', UpdateAudioProgressView.as_view(), name='user-audio-progress-update'),
]