"""
Bible Views - Django REST Framework views for Bible operations
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..services.bible_service import BibleService
from ..models import Language, Book, Testament

bible_service = BibleService()


# ==================== LANGUAGE VIEWS ====================

class LanguagesView(APIView):
    """Get all available languages for Bible reading"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get all active languages for Bible text",
        operation_summary="Get available languages",
        tags=['Bible'],
        responses={
            200: openapi.Response(
                description="List of languages",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'code': openapi.Schema(type=openapi.TYPE_STRING),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'native_name': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def get(self, request):
        """Get all active languages"""
        try:
            languages = bible_service.get_languages()
            return Response({
                'status': 'success',
                'data': languages
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== BOOKS VIEWS ====================

class BooksByLanguageView(APIView):
    """Get all books available in a specific language"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get all books that have content in the specified language",
        operation_summary="Get books by language",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code (en, am, or, ti)",
                type=openapi.TYPE_STRING,
                default='en',
                enum=['en', 'am', 'or', 'ti']
            )
        ],
        responses={
            200: openapi.Response(
                description="List of books in the selected language",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'language': openapi.Schema(type=openapi.TYPE_STRING),
                        'books': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'testament': openapi.Schema(type=openapi.TYPE_STRING),
                                    'chapters': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        )
                    }
                )
            ),
            404: openapi.Response(description="Language not found"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request):
        """Get books by language"""
        try:
            language = request.query_params.get('language', 'en')
            
            books = bible_service.get_books_by_language(language)
            
            if not books:
                return Response({
                    'status': 'error',
                    'message': f'Language "{language}" not found or no books available'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'status': 'success',
                'language': language,
                'books': books
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BooksByTestamentView(APIView):
    """Get books by testament with chapter counts"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get books by testament name (Old or New)",
        operation_summary="Get books by testament",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code",
                type=openapi.TYPE_STRING,
                default='en'
            )
        ],
        responses={
            200: openapi.Response(description="List of books"),
            400: openapi.Response(description="Invalid testament name"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request, testament_name):
        """Get books by testament"""
        if testament_name not in ['Old', 'New']:
            return Response({
                'status': 'error',
                'message': 'Testament must be "Old" or "New"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            language = request.query_params.get('language', 'en')
            
            books = bible_service.get_books_by_testament_with_language(testament_name, language)
            
            return Response({
                'status': 'success',
                'testament': testament_name,
                'language': language,
                'books': books
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookFullContentView(APIView):
    """Get full book content with all chapters and verses"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get complete book content with all chapters and verses",
        operation_summary="Get full book content",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code",
                type=openapi.TYPE_STRING,
                default='en'
            )
        ],
        responses={
            200: openapi.Response(description="Complete book with all verses"),
            404: openapi.Response(description="Book not found"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request, book_name):
        """Get full book content"""
        try:
            language = request.query_params.get('language', 'en')
            
            result = bible_service.get_book_full_content(book_name, language)
            
            if 'error' in result:
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Format response to match Flask API
            chapters_list = [
                {'chapter': ch['chapter'], 'verses': ch['verses']}
                for ch in result.get('chapters', [])
            ]
            
            return Response({
                'status': 'success',
                'book': book_name,
                'language': language,
                'chapters': chapters_list
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookChaptersView(APIView):
    """Get list of chapters (no content, just chapter numbers)"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get list of chapter numbers for a book",
        operation_summary="Get chapters list",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code",
                type=openapi.TYPE_STRING,
                default='en'
            )
        ],
        responses={
            200: openapi.Response(description="List of chapter numbers"),
            404: openapi.Response(description="Book not found"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request, book_name):
        """Get book chapters list"""
        try:
            language = request.query_params.get('language', 'en')
            
            result = bible_service.get_book_chapters_with_language(book_name, language)
            
            if 'error' in result:
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=status.HTTP_404_NOT_FOUND)
            
            chapters = result.get('chapters', [])
            chapter_numbers = [ch['chapter'] for ch in chapters]
            
            return Response({
                'status': 'success',
                'book': book_name,
                'total_chapters': len(chapter_numbers),
                'chapters': chapter_numbers
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChapterContentView(APIView):
    """Get specific chapter content"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get content of a specific chapter",
        operation_summary="Get chapter content",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code",
                type=openapi.TYPE_STRING,
                default='en'
            )
        ],
        responses={
            200: openapi.Response(description="Chapter with all verses"),
            404: openapi.Response(description="Chapter not found"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request, book_name, chapter_number):
        """Get chapter content"""
        try:
            language = request.query_params.get('language', 'en')
            
            result = bible_service.get_chapter_verses(book_name, chapter_number, language)
            
            if 'error' in result:
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=status.HTTP_404_NOT_FOUND)
            
            verses = result.get('verses', [])
            
            return Response({
                'status': 'success',
                'book': book_name,
                'chapter': chapter_number,
                'language': language,
                'verses': verses
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SpecificVerseView(APIView):
    """Get specific verse"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get a specific verse from the Bible",
        operation_summary="Get specific verse",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code",
                type=openapi.TYPE_STRING,
                default='en'
            )
        ],
        responses={
            200: openapi.Response(description="Specific verse text"),
            404: openapi.Response(description="Verse not found"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request, book_name, chapter_number, verse_number):
        """Get specific verse"""
        try:
            language = request.query_params.get('language', 'en')
            
            result = bible_service.get_specific_verse(book_name, chapter_number, verse_number, language)
            
            if 'error' in result:
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'status': 'success',
                'book': book_name,
                'chapter': chapter_number,
                'verse': verse_number,
                'language': language,
                'text': result['text']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== SEARCH & UTILITY VIEWS ====================

class SearchVersesView(APIView):
    """Search for verses containing specific text"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Search for verses containing specific text",
        operation_summary="Search verses",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'q',
                openapi.IN_QUERY,
                description="Search query",
                type=openapi.TYPE_STRING,
                required=True
            ),
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code",
                type=openapi.TYPE_STRING,
                default='en'
            ),
            openapi.Parameter(
                'limit',
                openapi.IN_QUERY,
                description="Maximum number of results",
                type=openapi.TYPE_INTEGER,
                default=50
            )
        ],
        responses={
            200: openapi.Response(description="Search results"),
            400: openapi.Response(description="Missing search query"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request):
        """Search verses"""
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({
                'status': 'error',
                'message': 'Search query is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            language = request.query_params.get('language', 'en')
            limit = int(request.query_params.get('limit', 50))
            
            results = bible_service.search_verses(query, language, limit)
            
            return Response({
                'status': 'success',
                'query': query,
                'results': results,
                'total': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RandomVerseView(APIView):
    """Get a random Bible verse"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get a random Bible verse",
        operation_summary="Random verse",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code",
                type=openapi.TYPE_STRING,
                default='en'
            ),
            openapi.Parameter(
                'testament',
                openapi.IN_QUERY,
                description="Filter by testament (Old or New)",
                type=openapi.TYPE_STRING,
                enum=['Old', 'New']
            )
        ],
        responses={
            200: openapi.Response(description="Random verse"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request):
        """Get random verse"""
        try:
            language = request.query_params.get('language', 'en')
            testament = request.query_params.get('testament')
            
            verse = bible_service.get_random_verse(language, testament)
            
            if 'error' in verse:
                return Response({
                    'status': 'error',
                    'message': verse['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'status': 'success',
                'data': verse
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerseOfTheDayView(APIView):
    """Get verse of the day"""
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get the verse of the day based on current date",
        operation_summary="Verse of the day",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'language',
                openapi.IN_QUERY,
                description="Language code",
                type=openapi.TYPE_STRING,
                default='en'
            )
        ],
        responses={
            200: openapi.Response(description="Verse of the day"),
            500: openapi.Response(description="Server error")
        }
    )
    def get(self, request):
        """Get verse of the day"""
        try:
            language = request.query_params.get('language', 'en')
            
            verse = bible_service.get_verse_of_the_day(language)
            
            if 'error' in verse:
                return Response({
                    'status': 'error',
                    'message': verse['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'status': 'success',
                'data': verse
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)