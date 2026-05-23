"""
Quiz Serializers
"""

from rest_framework import serializers


class BookLevelsSerializer(serializers.Serializer):
    """Serializer for book levels response"""
    book_id = serializers.IntegerField()
    book_name = serializers.CharField()
    levels = serializers.ListField()
    
    class Meta:
        ref_name = 'QuizBookLevelsSerializer'


class QuizStartSerializer(serializers.Serializer):
    """Serializer for starting a quiz - renamed to avoid conflict"""
    book_id = serializers.IntegerField()
    level_id = serializers.IntegerField()
    language_id = serializers.IntegerField()
    
    class Meta:
        ref_name = 'QuizStartSerializer'


class QuizOptionSerializer(serializers.Serializer):
    """Serializer for question options"""
    label = serializers.CharField(max_length=1)
    text = serializers.CharField()
    
    class Meta:
        ref_name = 'QuizOptionSerializer'


class QuizQuestionSerializer(serializers.Serializer):
    """Serializer for quiz question"""
    question_id = serializers.IntegerField()
    text = serializers.CharField()
    verse_reference = serializers.CharField(allow_null=True, allow_blank=True)
    options = QuizOptionSerializer(many=True)
    
    class Meta:
        ref_name = 'QuizQuestionSerializer'


class QuizNextQuestionSerializer(serializers.Serializer):
    """Serializer for next question response"""
    attempt_id = serializers.IntegerField()
    question_number = serializers.IntegerField()
    remaining_questions = serializers.IntegerField()
    question = QuizQuestionSerializer()
    
    class Meta:
        ref_name = 'QuizNextQuestionSerializer'


class QuizSubmitAnswerSerializer(serializers.Serializer):
    """Serializer for submitting an answer"""
    attempt_id = serializers.IntegerField()
    question_id = serializers.IntegerField()
    selected_option = serializers.CharField(max_length=1)
    
    class Meta:
        ref_name = 'QuizSubmitAnswerSerializer'


class QuizProgressSerializer(serializers.Serializer):
    """Serializer for quiz progress"""
    current = serializers.IntegerField()
    total = serializers.IntegerField()
    remaining = serializers.IntegerField()
    percentage = serializers.FloatField()
    
    class Meta:
        ref_name = 'QuizProgressSerializer'


class QuizSubmitAnswerResponseSerializer(serializers.Serializer):
    """Serializer for submit answer response"""
    is_correct = serializers.BooleanField()
    selected_option = serializers.CharField()
    correct_option = serializers.DictField()
    verse_reference = serializers.CharField()
    explanation = serializers.CharField()
    verse_text = serializers.CharField(allow_blank=True)
    progress = QuizProgressSerializer()
    next_available = serializers.BooleanField()
    
    class Meta:
        ref_name = 'QuizSubmitAnswerResponseSerializer'


class QuizFinishSerializer(serializers.Serializer):
    """Serializer for finish quiz response"""
    attempt_id = serializers.IntegerField()
    score_percentage = serializers.FloatField()
    correct_answers = serializers.IntegerField()
    wrong_answers = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    status = serializers.CharField()
    
    class Meta:
        ref_name = 'QuizFinishSerializer'


class QuizSummarySerializer(serializers.Serializer):
    """Serializer for quiz summary"""
    score_percentage = serializers.FloatField()
    correct_answers = serializers.IntegerField()
    wrong_answers = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    
    class Meta:
        ref_name = 'QuizSummarySerializer'


class QuizReviewQuestionSerializer(serializers.Serializer):
    """Serializer for review question"""
    question_id = serializers.IntegerField()
    question = serializers.CharField()
    selected_option = serializers.CharField(allow_null=True)
    correct_option = serializers.CharField()
    is_correct = serializers.BooleanField()
    verse_reference = serializers.CharField()
    explanation = serializers.CharField()
    
    class Meta:
        ref_name = 'QuizReviewQuestionSerializer'


class QuizReviewSerializer(serializers.Serializer):
    """Serializer for quiz review response"""
    attempt_id = serializers.IntegerField()
    summary = QuizSummarySerializer()
    questions = QuizReviewQuestionSerializer(many=True)
    
    class Meta:
        ref_name = 'QuizReviewSerializer'