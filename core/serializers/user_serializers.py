"""
User Serializers
"""

from rest_framework import serializers
from .auth_serializers import UserProfileSerializer


class CompleteUserProfileSerializer(serializers.Serializer):
    user = serializers.DictField()
    statistics = serializers.DictField()
    quiz_history = serializers.ListField(child=serializers.DictField())
    in_progress_quizzes = serializers.ListField(child=serializers.DictField())
    book_progress = serializers.ListField(child=serializers.DictField())
    recent_activity = serializers.ListField(child=serializers.DictField())
    can_resume = serializers.BooleanField()


class QuizHistorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    book_name = serializers.CharField(allow_null=True)
    testament = serializers.CharField(allow_null=True)
    total_questions = serializers.IntegerField()
    answered_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    score_percentage = serializers.FloatField()
    status = serializers.CharField()
    started_at = serializers.DateTimeField()
    completed_at = serializers.DateTimeField()


class InProgressQuizSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    book_name = serializers.CharField(allow_null=True)
    testament = serializers.CharField(allow_null=True)
    total_questions = serializers.IntegerField()
    answered_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    score_percentage = serializers.FloatField()
    started_at = serializers.DateTimeField()
    resume_data = serializers.DictField(allow_null=True, required=False)


class BookProgressSerializer(serializers.Serializer):
    book_name = serializers.CharField()
    testament = serializers.CharField(allow_null=True)
    current_chapter = serializers.IntegerField()
    current_verse = serializers.IntegerField()
    questions_answered = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    audio_current_position = serializers.IntegerField()
    audio_completed_chapters = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
    audio_progress_percentage = serializers.IntegerField()
    total_audio_chapters = serializers.IntegerField()
    last_activity = serializers.DateTimeField()
    completed = serializers.BooleanField()


class UserQuizProgressSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    book_name = serializers.CharField(allow_null=True)
    testament = serializers.CharField(allow_null=True)
    total_quizzes_taken = serializers.IntegerField()
    completed_quizzes = serializers.IntegerField()
    in_progress_attempt_id = serializers.IntegerField(allow_null=True)
    status = serializers.CharField(allow_null=True)
    total_questions = serializers.IntegerField()
    answered_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    score_percentage = serializers.FloatField()
    progress_percentage = serializers.IntegerField()
    can_resume = serializers.BooleanField()
    resume_data = serializers.DictField(allow_null=True, required=False)
    last_attempt_at = serializers.DateTimeField(allow_null=True)


class UserStatisticsSerializer(serializers.Serializer):
    total_quizzes = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    accuracy = serializers.FloatField()
    average_score = serializers.FloatField()
    best_score = serializers.FloatField()
    favorite_book = serializers.CharField(allow_null=True, required=False)
    books_started = serializers.IntegerField()
    books_completed = serializers.IntegerField()


class UserStartQuizSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()
    level_id = serializers.IntegerField(required=False, allow_null=True)
    language_id = serializers.IntegerField(required=False, allow_null=True)
    total_questions = serializers.IntegerField(required=False, default=10)


class UserSubmitAnswerSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    selected_option = serializers.CharField(max_length=1)
    is_correct = serializers.BooleanField(required=False, default=False)


class CompleteQuizSerializer(serializers.Serializer):
    attempt_id = serializers.IntegerField()
