"""
Admin URLs - Admin management endpoints
"""

from django.urls import path
from ..views.admin import (
    AdminBooksView, AdminBookDetailView,
    AdminLanguagesView, AdminLanguageDetailView,
    AdminUsersView, AdminUsersStatsView, AdminUserDetailView, AdminUserAdminView, AdminUserProgressView,
    AdminBibleImportView, AdminQuestionsImportView
)

urlpatterns = [
    # Book management
    path('books', AdminBooksView.as_view(), name='admin-books'),
    path('books/<int:book_id>', AdminBookDetailView.as_view(), name='admin-book-detail'),
    
    # Language management
    path('languages', AdminLanguagesView.as_view(), name='admin-languages'),
    path('languages/<int:language_id>', AdminLanguageDetailView.as_view(), name='admin-language-detail'),
    
    # User management
    path('users', AdminUsersView.as_view(), name='admin-users'),
    path('users/stats', AdminUsersStatsView.as_view(), name='admin-users-stats'),
    path('users/<int:user_id>', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('users/<int:user_id>/admin', AdminUserAdminView.as_view(), name='admin-user-admin'),
    path('users/<int:user_id>/progress', AdminUserProgressView.as_view(), name='admin-user-progress'),
    
    # Import management
    path('import/bible', AdminBibleImportView.as_view(), name='admin-import-bible'),
    path('import/questions', AdminQuestionsImportView.as_view(), name='admin-import-questions'),
    path('import/status', AdminBibleImportView.as_view(), name='admin-import-status'),
]