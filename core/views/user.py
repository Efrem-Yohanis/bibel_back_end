from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..services.user_profile_service import UserProfileService
from ..services.auth_service import AuthService
from ..serializers.user_serializers import (
    UserProfileSerializer, 
    CompleteUserProfileSerializer, 
    QuizHistorySerializer,
    UserStartQuizSerializer,
    UserSubmitAnswerSerializer,
    CompleteQuizSerializer,
    BookProgressSerializer, 
    UserStatisticsSerializer, 
    InProgressQuizSerializer,
    UserQuizProgressSerializer
)
from ..serializers.auth_serializers import ChangePasswordSerializer

user_profile_service = UserProfileService()
auth_service = AuthService()


# ==================== USER PROFILE (Tag: User) ====================

class UserProfileView(APIView):
    """Get/Update user profile"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user profile",
        operation_summary="Get User Profile",
        tags=['User'],
        responses={200: UserProfileSerializer()}
    )
    def get(self, request):
        """GET /api/user/profile - Get user profile"""
        user = request.user
        return Response({
            'status': 'success',
            'data': {
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
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update user profile",
        operation_summary="Update Profile",
        tags=['User'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={200: UserProfileSerializer()}
    )
    def put(self, request):
        """PUT /api/user/profile - Update user profile"""
        username = request.data.get('username')
        email = request.data.get('email')
        
        user, error = auth_service.update_user_profile(
            user_id=request.user.id,
            username=username,
            email=email
        )
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': 'Profile updated successfully',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Change user password",
        operation_summary="Change Password",
        tags=['User'],
        request_body=ChangePasswordSerializer,
        responses={200: 'Password changed successfully'}
    )
    def post(self, request):
        """POST /api/user/change-password - Change user password"""
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        success, error = auth_service.change_password(
            user_id=request.user.id,
            old_password=data['old_password'],
            new_password=data['new_password']
        )
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class UserCompleteProfileView(APIView):
    """Get complete user profile with statistics and history"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get complete user profile with statistics and history",
        operation_summary="Get Complete Profile",
        tags=['User'],
        responses={200: CompleteUserProfileSerializer()}
    )
    def get(self, request):
        """GET /api/user/complete-profile - Get complete profile"""
        profile = user_profile_service.get_user_complete_profile(request.user.id)
        
        if 'error' in profile:
            return Response({
                'status': 'error',
                'message': profile['error']
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'status': 'success',
            'data': profile
        }, status=status.HTTP_200_OK)


class UserStatisticsView(APIView):
    """Get aggregated user statistics"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get aggregated user statistics",
        operation_summary="Get User Statistics",
        tags=['User'],
        responses={200: UserStatisticsSerializer()}
    )
    def get(self, request):
        """GET /api/user/statistics - Get user statistics"""
        stats = user_profile_service.get_user_statistics(request.user.id)
        
        if 'error' in stats:
            return Response({
                'status': 'error',
                'message': stats['error']
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'status': 'success',
            'data': stats
        }, status=status.HTTP_200_OK)


class QuizHistoryView(APIView):
    """Get user's quiz history"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user's quiz history",
        operation_summary="Get Quiz History",
        tags=['User'],
        responses={200: QuizHistorySerializer(many=True)}
    )
    def get(self, request):
        """GET /api/user/quiz-history - Get quiz history"""
        history = user_profile_service.get_quiz_history(request.user.id)
        
        return Response({
            'status': 'success',
            'data': history
        }, status=status.HTTP_200_OK)


class InProgressQuizzesView(APIView):
    """Get user's in-progress quizzes"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get quizzes that can be resumed",
        operation_summary="Get In-Progress Quizzes",
        tags=['User'],
        responses={200: InProgressQuizSerializer(many=True)}
    )
    def get(self, request):
        """GET /api/user/in-progress - Get in-progress quizzes"""
        quizzes = user_profile_service.get_in_progress_quizzes(request.user.id)
        
        return Response({
            'status': 'success',
            'data': quizzes,
            'can_resume': len(quizzes) > 0
        }, status=status.HTTP_200_OK)


class BookProgressView(APIView):
    """Get user's progress through books"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user's progress through each book",
        operation_summary="Get Book Progress",
        tags=['User'],
        responses={200: BookProgressSerializer(many=True)}
    )
    def get(self, request):
        """GET /api/user/book-progress - Get book progress"""
        progress = user_profile_service.get_book_progress(request.user.id)
        
        return Response({
            'status': 'success',
            'data': progress
        }, status=status.HTTP_200_OK)


class UserQuizProgressView(APIView):
    """Get user's quiz progress for a specific book"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get user's quiz progress for a book",
        operation_summary="Get Quiz Progress",
        tags=['User', 'Quiz'],
        responses={200: UserQuizProgressSerializer()}
    )
    def get(self, request, book_id):
        """GET /api/user/quiz-progress/{book_id} - Get quiz progress for a book"""
        progress = user_profile_service.get_quiz_progress(request.user.id, book_id)

        return Response({
            'status': 'success',
            'data': progress
        }, status=status.HTTP_200_OK)


class UpdateBookProgressView(APIView):
    """Update user's progress in a book"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Update user's reading progress in a book",
        operation_summary="Update Book Progress",
        tags=['User'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['book_id', 'chapter', 'verse'],
            properties={
                'book_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'chapter': openapi.Schema(type=openapi.TYPE_INTEGER),
                'verse': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        responses={200: "Progress updated"}
    )
    def post(self, request):
        """POST /api/user/update-progress - Update reading progress"""
        book_id = request.data.get('book_id')
        chapter = request.data.get('chapter')
        verse = request.data.get('verse')
        
        if not all([book_id, chapter, verse]):
            return Response({
                'status': 'error',
                'message': 'book_id, chapter, and verse are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success = user_profile_service.update_book_progress(
            user_id=request.user.id,
            book_id=book_id,
            chapter=chapter,
            verse=verse
        )
        
        if not success:
            return Response({
                'status': 'error',
                'message': 'Failed to update progress'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': 'Progress updated successfully'
        }, status=status.HTTP_200_OK)


# ==================== QUIZ ACTIONS (Tag: Quiz) ====================

class StartQuizView(APIView):
    """Start a new quiz"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Start a new quiz session",
        operation_summary="Start Quiz",
        tags=['Quiz'],
        request_body=UserStartQuizSerializer,  # Fixed: Use UserStartQuizSerializer
        responses={200: "Quiz started"}
    )
    def post(self, request):
        """POST /api/user/quiz/start - Start a new quiz"""
        serializer = UserStartQuizSerializer(data=request.data)  # Fixed: Use UserStartQuizSerializer
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result = user_profile_service.start_new_quiz(
            user_id=request.user.id,
            book_id=data['book_id'],
            level_id=data.get('level_id'),
            language_id=data.get('language_id'),
            total_questions=data.get('total_questions', 10)
        )
        
        if 'error' in result:
            return Response({
                'status': 'error',
                'message': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)


class SubmitAnswerView(APIView):
    """Submit an answer for a quiz"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Submit an answer for a quiz",
        operation_summary="Submit Answer",
        tags=['Quiz'],
        request_body=UserSubmitAnswerSerializer,  # Fixed: Use UserSubmitAnswerSerializer
        responses={200: "Answer saved"}
    )
    def post(self, request):
        """POST /api/user/quiz/submit-answer - Submit answer"""
        serializer = UserSubmitAnswerSerializer(data=request.data)  # Fixed: Use UserSubmitAnswerSerializer
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        success = user_profile_service.save_quiz_answer(
            attempt_id=data['attempt_id'],
            question_data=data
        )
        
        if not success:
            return Response({
                'status': 'error',
                'message': 'Failed to save answer'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'message': 'Answer saved successfully'
        }, status=status.HTTP_200_OK)


class CompleteQuizView(APIView):
    """Complete a quiz and update statistics"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Complete a quiz and update user statistics",
        operation_summary="Complete Quiz",
        tags=['Quiz'],
        request_body=CompleteQuizSerializer,
        responses={200: "Quiz completed"}
    )
    def post(self, request):
        """POST /api/user/quiz/complete - Complete quiz"""
        serializer = CompleteQuizSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = user_profile_service.complete_quiz(
            attempt_id=serializer.validated_data['attempt_id']
        )
        
        if 'error' in result:
            return Response({
                'status': 'error',
                'message': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)


class ResumeQuizView(APIView):
    """Resume an in-progress quiz"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Resume an in-progress quiz",
        operation_summary="Resume Quiz",
        tags=['Quiz'],
        manual_parameters=[
            openapi.Parameter('attempt_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True)
        ],
        responses={200: "Quiz data to resume"}
    )
    def get(self, request):
        """GET /api/user/quiz/resume - Resume quiz"""
        attempt_id = request.query_params.get('attempt_id')
        
        if not attempt_id:
            return Response({
                'status': 'error',
                'message': 'attempt_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = user_profile_service.resume_quiz(int(attempt_id))
        
        if 'error' in result:
            return Response({
                'status': 'error',
                'message': result['error']
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'status': 'success',
            'data': result
        }, status=status.HTTP_200_OK)