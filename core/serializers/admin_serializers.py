"""
Admin Serializers
"""

from rest_framework import serializers


# ==================== BOOK MANAGEMENT ====================

class BookListSerializer(serializers.Serializer):
    """Serializer for book list"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    testament = serializers.CharField(allow_null=True)
    chapters = serializers.IntegerField()
    verses = serializers.IntegerField()
    
    class Meta:
        ref_name = 'AdminBookListSerializer'


class BookDetailSerializer(serializers.Serializer):
    """Serializer for book detail"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    testament = serializers.CharField(allow_null=True)
    chapters = serializers.IntegerField()
    verses = serializers.IntegerField()
    
    class Meta:
        ref_name = 'AdminBookDetailSerializer'


class BookCreateSerializer(serializers.Serializer):
    """Serializer for creating a book"""
    name = serializers.CharField(max_length=100)
    testament = serializers.CharField(max_length=50)
    
    class Meta:
        ref_name = 'AdminBookCreateSerializer'


class BookUpdateSerializer(serializers.Serializer):
    """Serializer for updating a book"""
    name = serializers.CharField(max_length=100, required=False)
    testament = serializers.CharField(max_length=50, required=False)
    
    class Meta:
        ref_name = 'AdminBookUpdateSerializer'


# ==================== LANGUAGE MANAGEMENT ====================

class LanguageListSerializer(serializers.Serializer):
    """Serializer for language list"""
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    native_name = serializers.CharField(allow_null=True)
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    
    class Meta:
        ref_name = 'AdminLanguageListSerializer'


class LanguageCreateSerializer(serializers.Serializer):
    """Serializer for creating a language"""
    code = serializers.CharField(max_length=10)
    name = serializers.CharField(max_length=50)
    native_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False, default=True)
    
    class Meta:
        ref_name = 'AdminLanguageCreateSerializer'


class LanguageUpdateSerializer(serializers.Serializer):
    """Serializer for updating a language"""
    code = serializers.CharField(max_length=10, required=False)
    name = serializers.CharField(max_length=50, required=False)
    native_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    
    class Meta:
        ref_name = 'AdminLanguageUpdateSerializer'


# ==================== USER MANAGEMENT ====================

class UserListSerializer(serializers.Serializer):
    """Serializer for user list"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    created_at = serializers.DateTimeField()
    last_login = serializers.DateTimeField(allow_null=True)
    is_active = serializers.BooleanField()
    is_admin = serializers.BooleanField()
    total_quizzes_taken = serializers.IntegerField()
    total_correct_answers = serializers.IntegerField()
    total_questions_answered = serializers.IntegerField()
    
    class Meta:
        ref_name = 'AdminUserListSerializer'


class UserDetailSerializer(serializers.Serializer):
    """Serializer for user detail"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    created_at = serializers.DateTimeField()
    last_login = serializers.DateTimeField(allow_null=True)
    is_active = serializers.BooleanField()
    is_admin = serializers.BooleanField()
    total_quizzes_taken = serializers.IntegerField()
    total_correct_answers = serializers.IntegerField()
    total_questions_answered = serializers.IntegerField()
    
    class Meta:
        ref_name = 'AdminUserDetailSerializer'


class UserProgressSerializer(serializers.Serializer):
    """Serializer for user quiz progress"""
    quiz_attempts = serializers.ListField()
    book_progress = serializers.ListField()
    total_quizzes = serializers.IntegerField()
    total_books_progress = serializers.IntegerField()
    
    class Meta:
        ref_name = 'AdminUserProgressSerializer'


class UserStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating user status"""
    is_active = serializers.BooleanField()
    
    class Meta:
        ref_name = 'AdminUserStatusUpdateSerializer'


class UserAdminUpdateSerializer(serializers.Serializer):
    """Serializer for updating user admin status"""
    is_admin = serializers.BooleanField()
    
    class Meta:
        ref_name = 'AdminUserAdminUpdateSerializer'


class UserStatsSummarySerializer(serializers.Serializer):
    """Serializer for user statistics summary"""
    total_users = serializers.IntegerField()
    total_quizzes = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    avg_quizzes_per_user = serializers.FloatField()
    
    class Meta:
        ref_name = 'AdminUserStatsSummarySerializer'


# ==================== IMPORT MANAGEMENT ====================

class BibleImportSerializer(serializers.Serializer):
    """Serializer for Bible import"""
    file_path = serializers.CharField()
    language = serializers.CharField(max_length=10)
    
    class Meta:
        ref_name = 'AdminBibleImportSerializer'


class QuestionsImportSerializer(serializers.Serializer):
    """Serializer for questions import"""
    file = serializers.FileField()
    language = serializers.CharField(max_length=10)
    testament = serializers.CharField(max_length=10)
    book = serializers.CharField(max_length=100)
    
    class Meta:
        ref_name = 'AdminQuestionsImportSerializer'


class ImportStatusSerializer(serializers.Serializer):
    """Serializer for import status"""
    books_imported = serializers.IntegerField()
    verses_imported = serializers.IntegerField()
    verse_texts_by_language = serializers.DictField()
    languages_available = serializers.ListField()
    
    class Meta:
        ref_name = 'AdminImportStatusSerializer'


class QuestionsStatusSerializer(serializers.Serializer):
    """Serializer for questions status"""
    total_questions = serializers.IntegerField()
    questions_by_language = serializers.DictField()
    
    class Meta:
        ref_name = 'AdminQuestionsStatusSerializer'


class ImportResultSerializer(serializers.Serializer):
    """Serializer for import result"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    book_name = serializers.CharField(required=False)
    verses_imported = serializers.IntegerField(required=False)
    questions_imported = serializers.IntegerField(required=False)
    language = serializers.CharField(required=False)
    
    class Meta:
        ref_name = 'AdminImportResultSerializer'