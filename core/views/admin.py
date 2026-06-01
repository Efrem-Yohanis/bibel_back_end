"""
Admin Views - Admin management endpoints
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..services.admin_service import (
    AdminBookService, AdminLanguageService, AdminUserService,
    AdminBibleImportService, AdminQuestionsImportService
)
from ..serializers.admin_serializers import (
    BookListSerializer, BookCreateSerializer, BookUpdateSerializer,
    LanguageListSerializer, LanguageCreateSerializer, LanguageUpdateSerializer,
    UserListSerializer, UserDetailSerializer, UserProgressSerializer,
    UserStatusUpdateSerializer, UserAdminUpdateSerializer, UserStatsSummarySerializer,
    BibleImportSerializer, QuestionsImportSerializer, ImportStatusSerializer,
    QuestionsStatusSerializer, ImportResultSerializer
)

# Initialize services
book_service = AdminBookService()
language_service = AdminLanguageService()
user_service = AdminUserService()
bible_import_service = AdminBibleImportService()
questions_import_service = AdminQuestionsImportService()


# ==================== BOOK MANAGEMENT ====================

class AdminBooksView(APIView):
    """Admin book management - list all books"""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get all books (admin)",
        operation_summary="List Books",
        tags=['Admin'],
        manual_parameters=[
            openapi.Parameter('testament', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False)
        ],
        responses={200: BookListSerializer(many=True)}
    )
    def get(self, request):
        """GET /api/admin/books - List all books"""
        testament = request.query_params.get('testament')
        
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        books = book_service.get_all_books(testament)
        return Response({
            'success': True,
            'data': books
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Add a new book",
        operation_summary="Create Book",
        tags=['Admin'],
        request_body=BookCreateSerializer,
        responses={201: BookCreateSerializer}
    )
    def post(self, request):
        """POST /api/admin/books - Add a new book"""
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = BookCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result = book_service.add_book(
            name=data['name'],
            testament_name=data['testament']
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_201_CREATED)


class AdminBookDetailView(APIView):
    """Admin book management - get, update, delete single book"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Get book by ID",
        operation_summary="Get Book",
        tags=['Admin'],
        responses={200: BookListSerializer()}
    )
    def get(self, request, book_id):
        """GET /api/admin/books/{book_id} - Get book by ID"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        book = book_service.get_book_by_id(book_id)
        if not book:
            return Response({
                'success': False,
                'message': 'Book not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': book
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update book",
        operation_summary="Update Book",
        tags=['Admin'],
        request_body=BookUpdateSerializer,
        responses={200: 'Book updated'}
    )
    def put(self, request, book_id):
        """PUT /api/admin/books/{book_id} - Update book"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        serializer = BookUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result = book_service.update_book(
            book_id=book_id,
            name=data.get('name'),
            testament_name=data.get('testament')
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': result['message']
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Delete book",
        operation_summary="Delete Book",
        tags=['Admin'],
        responses={200: 'Book deleted'}
    )
    def delete(self, request, book_id):
        """DELETE /api/admin/books/{book_id} - Delete book"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        result = book_service.delete_book(book_id)
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': result['message']
        }, status=status.HTTP_200_OK)


# ==================== LANGUAGE MANAGEMENT ====================

class AdminLanguagesView(APIView):
    """Admin language management"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Get all languages",
        operation_summary="List Languages",
        tags=['Admin'],
        responses={200: LanguageListSerializer(many=True)}
    )
    def get(self, request):
        """GET /api/admin/languages - List all languages"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        languages = language_service.get_all_languages()
        return Response({
            'success': True,
            'data': languages
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Add a new language",
        operation_summary="Create Language",
        tags=['Admin'],
        request_body=LanguageCreateSerializer,
        responses={201: 'Language created'}
    )
    def post(self, request):
        """POST /api/admin/languages - Add a new language"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        serializer = LanguageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result = language_service.add_language(
            code=data['code'],
            name=data['name'],
            native_name=data.get('native_name')
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_201_CREATED)


class AdminLanguageDetailView(APIView):
    """Admin language management - update, delete"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Update language",
        operation_summary="Update Language",
        tags=['Admin'],
        request_body=LanguageUpdateSerializer,
        responses={200: 'Language updated'}
    )
    def put(self, request, language_id):
        """PUT /api/admin/languages/{language_id} - Update language"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        serializer = LanguageUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = language_service.update_language(
            language_id=language_id,
            **serializer.validated_data
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': result['message']
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Delete language",
        operation_summary="Delete Language",
        tags=['Admin'],
        responses={200: 'Language deleted'}
    )
    def delete(self, request, language_id):
        """DELETE /api/admin/languages/{language_id} - Delete language"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        result = language_service.delete_language(language_id)
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': result['message']
        }, status=status.HTTP_200_OK)


# ==================== USER MANAGEMENT ====================

class AdminUsersView(APIView):
    """Admin user management"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Get all users",
        operation_summary="List Users",
        tags=['Admin'],
        manual_parameters=[
            openapi.Parameter('limit', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=100),
            openapi.Parameter('offset', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, default=0)
        ],
        responses={200: UserListSerializer(many=True)}
    )
    def get(self, request):
        """GET /api/admin/users - List all users"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        users = user_service.get_all_users(limit, offset)
        total = user_service.get_user_count()
        
        return Response({
            'success': True,
            'data': {
                'users': users,
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }, status=status.HTTP_200_OK)


class AdminUsersStatsView(APIView):
    """Admin user statistics summary"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Get user statistics summary",
        operation_summary="User Stats",
        tags=['Admin'],
        responses={200: UserStatsSummarySerializer()}
    )
    def get(self, request):
        """GET /api/admin/users/stats - Get user statistics"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        stats = user_service.get_user_stats_summary()
        return Response({
            'success': True,
            'data': stats
        }, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    """Admin user management - get, update, delete single user"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Get user by ID",
        operation_summary="Get User",
        tags=['Admin'],
        responses={200: UserDetailSerializer()}
    )
    def get(self, request, user_id):
        """GET /api/admin/users/{user_id} - Get user by ID"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        user = user_service.get_user_by_id(user_id)
        if not user:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'data': user
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Toggle user active status",
        operation_summary="Toggle User Status",
        tags=['Admin'],
        request_body=UserStatusUpdateSerializer,
        responses={200: 'Status updated'}
    )
    def put(self, request, user_id):
        """PUT /api/admin/users/{user_id}/status - Update user status"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        serializer = UserStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = user_service.toggle_user_status(
            user_id=user_id,
            is_active=serializer.validated_data['is_active']
        )
        
        if not result:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'message': 'User status updated'
        }, status=status.HTTP_200_OK)


class AdminUserAdminView(APIView):
    """Admin user management - promote/demote admin"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Update user admin status",
        operation_summary="Update Admin Status",
        tags=['Admin'],
        request_body=UserAdminUpdateSerializer,
        responses={200: 'Admin status updated'}
    )
    def put(self, request, user_id):
        """PUT /api/admin/users/{user_id}/admin - Update admin status"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        serializer = UserAdminUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        result = user_service.set_user_admin_status(
            user_id=user_id,
            is_admin=serializer.validated_data['is_admin']
        )
        
        if not result:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'message': 'Admin status updated'
        }, status=status.HTTP_200_OK)


class AdminUserProgressView(APIView):
    """Admin user progress view"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Get user quiz progress",
        operation_summary="Get User Progress",
        tags=['Admin'],
        responses={200: UserProgressSerializer()}
    )
    def get(self, request, user_id):
        """GET /api/admin/users/{user_id}/progress - Get user progress"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        progress = user_service.get_user_quiz_progress(user_id)
        return Response({
            'success': True,
            'data': progress
        }, status=status.HTTP_200_OK)


# ==================== IMPORT MANAGEMENT ====================

class AdminBibleImportView(APIView):
    """Admin Bible import"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Get import status",
        operation_summary="Import Status",
        tags=['Admin'],
        responses={200: ImportStatusSerializer()}
    )
    def get(self, request):
        """GET /api/admin/import/status - Get import status"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        status_data = bible_import_service.get_import_status()
        return Response({
            'success': True,
            'data': status_data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Import Bible file",
        operation_summary="Import Bible",
        tags=['Admin'],
        request_body=BibleImportSerializer,
        responses={200: ImportResultSerializer()}
    )
    def post(self, request):
        """POST /api/admin/import/bible - Import Bible file"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        serializer = BibleImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result = bible_import_service.import_book(
            file_path=data['file_path'],
            language_code=data['language']
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)


class AdminQuestionsImportView(APIView):
    """Admin questions import"""
    permission_classes = [IsAuthenticated]
    
    def check_admin(self, request):
        if not request.user.is_admin:
            return Response({
                'success': False,
                'message': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)
        return None
    
    @swagger_auto_schema(
        operation_description="Get questions import status",
        operation_summary="Questions Status",
        tags=['Admin'],
        responses={200: QuestionsStatusSerializer()}
    )
    def get(self, request):
        """GET /api/admin/import/questions/status - Get questions status"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        status_data = questions_import_service.get_questions_status()
        return Response({
            'success': True,
            'data': status_data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Import questions JSON file",
        operation_summary="Import Questions",
        tags=['Admin'],
        request_body=QuestionsImportSerializer,
        responses={200: ImportResultSerializer()}
    )
    def post(self, request):
        """POST /api/admin/import/questions - Import questions file"""
        admin_check = self.check_admin(request)
        if admin_check:
            return admin_check
        
        serializer = QuestionsImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        result = questions_import_service.import_questions_json(
            file_path=data['file_path'],
            language_code=data['language']
        )
        
        if not result['success']:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)