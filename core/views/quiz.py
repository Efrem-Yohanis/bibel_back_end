"""
Quiz Views - Quiz management endpoints
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..services.quiz_service import QuizService
from ..serializers.quiz_serializers import (
    BookLevelsSerializer,
    QuizStartSerializer,
    QuizSubmitAnswerSerializer,
    QuizFinishSerializer,
    QuizReviewSerializer
)

quiz_service = QuizService()


# ==================== BOOK LEVELS ====================

class BookLevelsView(APIView):
    """Get available quiz levels for a specific book"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get available difficulty levels for a book",
        operation_summary="Get Book Levels",
        tags=['Quiz'],
        manual_parameters=[
            openapi.Parameter('book_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: BookLevelsSerializer}
    )
    def get(self, request, book_id):
        """GET /api/quiz/books/{book_id}/levels"""
        result = quiz_service.get_book_levels(book_id)
        
        if 'error' in result:
            return Response({
                'success': False,
                'message': result['error']
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)


# ==================== START QUIZ ====================

class StartQuizView(APIView):
    """Start a new quiz session"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Start a new quiz session for a specific book and level",
        operation_summary="Start Quiz",
        tags=['Quiz'],
        request_body=QuizStartSerializer,
        responses={201: 'Quiz started successfully'}
    )
    def post(self, request):
        """POST /api/quiz/start"""
        serializer = QuizStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result = quiz_service.start_quiz(
            user_id=request.user.id,
            book_id=data['book_id'],
            level_id=data['level_id'],
            language_id=data['language_id']
        )
        
        if 'error' in result:
            return Response({
                'success': False,
                'message': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_201_CREATED)


# ==================== GET NEXT QUESTION ====================

class NextQuestionView(APIView):
    """Get the next question in the quiz"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get the next question for the quiz (one at a time)",
        operation_summary="Get Next Question",
        tags=['Quiz'],
        manual_parameters=[
            openapi.Parameter('attempt_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: 'Next question or completion status'}
    )
    def get(self, request, attempt_id):
        """GET /api/quiz/{attempt_id}/next"""
        result = quiz_service.get_next_question(attempt_id, request.user.id)
        
        if 'error' in result:
            return Response({
                'success': False,
                'message': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if result.get('completed'):
            return Response({
                'success': True,
                'data': {
                    'completed': True,
                    'message': 'Quiz completed'
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)


# ==================== SUBMIT ANSWER ====================

class SubmitAnswerView(APIView):
    """Submit an answer for the current question"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Submit an answer for the current question",
        operation_summary="Submit Answer",
        tags=['Quiz'],
        request_body=QuizSubmitAnswerSerializer,
        responses={200: 'Answer processed'}
    )
    def post(self, request):
        """POST /api/quiz/answer"""
        serializer = QuizSubmitAnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result = quiz_service.submit_answer(
            attempt_id=data['attempt_id'],
            user_id=request.user.id,
            question_id=data['question_id'],
            selected_option=data['selected_option']
        )
        
        if 'error' in result:
            return Response({
                'success': False,
                'message': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)


# ==================== FINISH QUIZ ====================

class FinishQuizView(APIView):
    """Finish the quiz and get final score"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Complete the quiz and calculate final score",
        operation_summary="Finish Quiz",
        tags=['Quiz'],
        manual_parameters=[
            openapi.Parameter('attempt_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: QuizFinishSerializer}
    )
    def post(self, request, attempt_id):
        """POST /api/quiz/{attempt_id}/finish"""
        result = quiz_service.finish_quiz(attempt_id, request.user.id)
        
        if 'error' in result:
            return Response({
                'success': False,
                'message': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)


# ==================== QUIZ REVIEW ====================

class QuizReviewView(APIView):
    """Get full quiz review with all answers and explanations"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get full quiz review with all questions, answers, and explanations",
        operation_summary="Get Quiz Review",
        tags=['Quiz'],
        manual_parameters=[
            openapi.Parameter('attempt_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: QuizReviewSerializer}
    )
    def get(self, request, attempt_id):
        """GET /api/quiz/{attempt_id}/review"""
        result = quiz_service.get_quiz_review(attempt_id, request.user.id)
        
        if 'error' in result:
            return Response({
                'success': False,
                'message': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
