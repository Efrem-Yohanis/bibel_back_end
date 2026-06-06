"""
Bible Views — Django REST Framework views for Bible operations with Audio Support.

Design conventions used throughout:
  - BibleService is instantiated per-request (via get_service()) rather than
    at module level, avoiding shared mutable state across requests.
  - Service methods signal "not found" / "bad input" by returning a dict with
    an 'error' key AND an optional 'code' key ('not_found' | 'bad_request' |
    'server_error').  Views inspect the code to choose the HTTP status.
  - Input validation (type coercion, allowed values) is done in the view
    before calling the service, returning HTTP 400 immediately.
  - A shared _error_response() helper keeps response shape consistent.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..services.bible_service import BibleService

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_ERR_SCHEMA = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'status': openapi.Schema(type=openapi.TYPE_STRING, example='error'),
        'message': openapi.Schema(type=openapi.TYPE_STRING),
    },
)

_LANG_PARAM = openapi.Parameter(
    'language', openapi.IN_QUERY,
    description="Language code (e.g. en, am, or, ti)",
    type=openapi.TYPE_STRING,
    default='en',
)


def get_service() -> BibleService:
    """Return a fresh BibleService instance for the current request."""
    return BibleService()


def _error_response(message: str, http_status: int) -> Response:
    """Uniform error response shape."""
    return Response({'status': 'error', 'message': message}, status=http_status)


def _service_error_to_response(result: dict) -> Response:
    """
    Convert a service error dict (with optional 'code' key) to an HTTP response.
    Defaults to 500 when the code is absent or unrecognised.
    """
    message = result.get('error', 'An unexpected error occurred')
    code = result.get('code', 'server_error')
    http_map = {
        'not_found': status.HTTP_404_NOT_FOUND,
        'bad_request': status.HTTP_400_BAD_REQUEST,
        'server_error': status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    return _error_response(message, http_map.get(code, status.HTTP_500_INTERNAL_SERVER_ERROR))


def _parse_positive_int(value, name: str, default: int = None):
    """
    Parse `value` as a positive integer.
    Returns (parsed_int, None) on success or (None, Response) on failure.
    """
    if value is None:
        if default is not None:
            return default, None
        return None, _error_response(f"'{name}' is required.", status.HTTP_400_BAD_REQUEST)
    try:
        parsed = int(value)
        if parsed <= 0:
            raise ValueError
        return parsed, None
    except (ValueError, TypeError):
        return None, _error_response(
            f"'{name}' must be a positive integer.", status.HTTP_400_BAD_REQUEST
        )


# ==================== LANGUAGE / TESTAMENT VIEWS ====================

class LanguagesView(APIView):
    """Get all available languages for Bible reading."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get available languages",
        operation_description="Get all active languages for Bible text.",
        tags=['Bible'],
        responses={
            200: openapi.Response(
                description="List of languages",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'code': openapi.Schema(type=openapi.TYPE_STRING),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'native_name': openapi.Schema(type=openapi.TYPE_STRING),
                                },
                            ),
                        ),
                    },
                ),
            ),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request):
        try:
            languages = get_service().get_languages()
            return Response({'status': 'success', 'data': languages}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class TestamentsView(APIView):
    """Get list of all testaments."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get available testaments",
        operation_description="Get all testaments (Old and New).",
        tags=['Bible'],
        responses={
            200: openapi.Response(
                description="List of testaments",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                },
                            ),
                        ),
                    },
                ),
            ),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request):
        try:
            testaments = get_service().get_testaments()
            return Response({'status': 'success', 'data': testaments}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== BOOK VIEWS ====================

class BooksByLanguageView(APIView):
    """Get all books available in a specific language."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get books by language",
        operation_description="Get all books that have content in the specified language.",
        tags=['Bible'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="List of books in the selected language"),
            404: openapi.Response(description="Language not found", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request):
        language = request.query_params.get('language', 'en')
        try:
            books = get_service().get_books_by_language(language)
            if books is None:
                return _error_response(
                    f'Language "{language}" not found', status.HTTP_404_NOT_FOUND
                )
            return Response(
                {'status': 'success', 'language': language, 'books': books},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class BooksByTestamentView(APIView):
    """Get books by testament with chapter counts."""
    permission_classes = [AllowAny]

    _VALID_TESTAMENTS = ('Old', 'New')

    @swagger_auto_schema(
        operation_summary="Get books by testament",
        operation_description="Get books by testament name (Old or New).",
        tags=['Bible'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="List of books"),
            400: openapi.Response(description="Invalid testament name", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request, testament_name):
        # Input validation before touching the service
        if testament_name not in self._VALID_TESTAMENTS:
            return _error_response(
                'Testament must be "Old" or "New"', status.HTTP_400_BAD_REQUEST
            )

        language = request.query_params.get('language', 'en')
        try:
            books = get_service().get_books_by_testament_with_language(testament_name, language)
            return Response(
                {
                    'status': 'success',
                    'testament': testament_name,
                    'language': language,
                    'books': books,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookFullContentView(APIView):
    """Get full book content with all chapters and verses (including audio info)."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get full book content",
        operation_description="Get complete book content with all chapters and verses.",
        tags=['Bible'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="Complete book with all verses"),
            404: openapi.Response(description="Book or language not found", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request, book_name):
        language = request.query_params.get('language', 'en')
        try:
            result = get_service().get_book_full_content(book_name, language)
            if 'error' in result:
                return _service_error_to_response(result)

            book_info = result.get('book_info', {})
            return Response(
                {
                    'status': 'success',
                    'book': book_info.get('name', book_name),
                    'book_id': book_info.get('id'),
                    'language': language,
                    'has_audio': book_info.get('has_audio', False),
                    'audio_info': result.get('audio_info', {}),
                    'chapters': result.get('chapters', []),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookChaptersView(APIView):
    """Get list of chapters for a book (no verse content, just chapter numbers)."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get chapters list",
        operation_description="Get list of chapter numbers for a book.",
        tags=['Bible'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="List of chapter numbers"),
            404: openapi.Response(description="Book or language not found", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request, book_name):
        language = request.query_params.get('language', 'en')
        try:
            result = get_service().get_book_chapters_with_language(book_name, language)
            if 'error' in result:
                return _service_error_to_response(result)

            chapter_numbers = [ch['chapter'] for ch in result.get('chapters', [])]
            return Response(
                {
                    'status': 'success',
                    'book': result.get('book_name', book_name),
                    'book_id': result.get('book_id'),
                    'total_chapters': len(chapter_numbers),
                    'has_audio': result.get('has_audio', False),
                    'chapters': chapter_numbers,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChapterContentView(APIView):
    """Get a specific chapter's content with audio."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get chapter content",
        operation_description="Get content of a specific chapter.",
        tags=['Bible'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="Chapter with all verses"),
            400: openapi.Response(description="Invalid chapter number", schema=_ERR_SCHEMA),
            404: openapi.Response(description="Chapter not found", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request, book_name, chapter_number):
        # Validate chapter_number is a positive integer before hitting the service
        chapter, err = _parse_positive_int(chapter_number, 'chapter_number')
        if err:
            return err

        language = request.query_params.get('language', 'en')
        try:
            result = get_service().get_chapter_verses(book_name, chapter, language)
            if 'error' in result:
                return _service_error_to_response(result)

            return Response(
                {
                    'status': 'success',
                    'book': result.get('book', book_name),
                    'book_id': result.get('book_id'),
                    'chapter': chapter,
                    'language': language,
                    'has_audio': result.get('has_audio', False),
                    'audio_url': result.get('audio_url'),
                    'verses': result.get('verses', []),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class SpecificVerseView(APIView):
    """Get a specific verse."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get specific verse",
        operation_description="Get a specific verse from the Bible.",
        tags=['Bible'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="Specific verse text"),
            400: openapi.Response(description="Invalid chapter or verse number", schema=_ERR_SCHEMA),
            404: openapi.Response(description="Verse not found", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request, book_name, chapter_number, verse_number):
        chapter, err = _parse_positive_int(chapter_number, 'chapter_number')
        if err:
            return err
        verse, err = _parse_positive_int(verse_number, 'verse_number')
        if err:
            return err

        language = request.query_params.get('language', 'en')
        try:
            result = get_service().get_specific_verse(book_name, chapter, verse, language)
            if 'error' in result:
                return _service_error_to_response(result)

            return Response(
                {
                    'status': 'success',
                    'book': result.get('book', book_name),
                    'book_id': result.get('book_id'),
                    'chapter': chapter,
                    'verse': verse,
                    'language': language,
                    'text': result['text'],
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== AUDIO VIEWS ====================

class BookAudioView(APIView):
    """Get audio information for a specific book."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get book audio",
        operation_description="Get audio information for a specific book.",
        tags=['Audio'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="Book audio information"),
            400: openapi.Response(description="Invalid book ID", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request, book_id):
        book_id_int, err = _parse_positive_int(book_id, 'book_id')
        if err:
            return err

        language = request.query_params.get('language', 'en')
        try:
            audio_info = get_service().get_book_audio(book_id_int, language)
            return Response(
                {'status': 'success', 'book_id': book_id_int, 'audio': audio_info},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChapterAudioView(APIView):
    """Get audio for a specific chapter."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Get chapter audio",
        operation_description="Get audio URL for a specific chapter.",
        tags=['Audio'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="Chapter audio information"),
            400: openapi.Response(description="Invalid book ID or chapter number", schema=_ERR_SCHEMA),
            404: openapi.Response(description="Audio not found", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request, book_id, chapter_number):
        book_id_int, err = _parse_positive_int(book_id, 'book_id')
        if err:
            return err
        chapter, err = _parse_positive_int(chapter_number, 'chapter_number')
        if err:
            return err

        language = request.query_params.get('language', 'en')
        try:
            result = get_service().get_chapter_audio(book_id_int, chapter, language)
            if not result.get('success'):
                return _error_response(
                    result.get('message', 'Audio not found'), status.HTTP_404_NOT_FOUND
                )
            return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserAudioProgressView(APIView):
    """Get user's audio progress for a book."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get audio progress",
        operation_description="Get user's audio listening progress for a book.",
        tags=['Audio', 'User'],
        responses={
            200: openapi.Response(description="User's audio progress"),
            400: openapi.Response(description="Invalid book ID", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request, book_id):
        book_id_int, err = _parse_positive_int(book_id, 'book_id')
        if err:
            return err

        try:
            result = get_service().get_user_audio_progress(request.user.id, book_id_int)
            return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateAudioProgressView(APIView):
    """Update user's audio progress."""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Update audio progress",
        operation_description="Update user's audio listening progress.",
        tags=['Audio', 'User'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['chapter_number'],
            properties={
                'chapter_number': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Current chapter number (positive integer)",
                ),
                'current_position': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Current playback position in seconds (≥ 0)",
                ),
                'completed_chapter': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Chapter just completed, if any (positive integer)",
                ),
            },
        ),
        responses={
            200: openapi.Response(description="Progress updated"),
            400: openapi.Response(description="Invalid or missing fields", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def post(self, request, book_id):
        book_id_int, err = _parse_positive_int(book_id, 'book_id')
        if err:
            return err

        # chapter_number — required, positive int
        chapter, err = _parse_positive_int(
            request.data.get('chapter_number'), 'chapter_number'
        )
        if err:
            return err

        # current_position — optional, non-negative int
        raw_position = request.data.get('current_position')
        current_position = None
        if raw_position is not None:
            try:
                current_position = int(raw_position)
                if current_position < 0:
                    raise ValueError
            except (ValueError, TypeError):
                return _error_response(
                    "'current_position' must be a non-negative integer.",
                    status.HTTP_400_BAD_REQUEST,
                )

        # completed_chapter — optional, positive int
        raw_completed = request.data.get('completed_chapter')
        completed_chapter = None
        if raw_completed is not None:
            completed_chapter, err = _parse_positive_int(raw_completed, 'completed_chapter')
            if err:
                return err

        language_code = request.query_params.get('language', 'en')
        try:
            result = get_service().update_audio_progress(
                user_id=request.user.id,
                book_id=book_id_int,
                chapter_number=chapter,
                current_position=current_position,
                completed_chapter=completed_chapter,
                language_code=language_code,
            )
            if not result.get('success'):
                return _error_response(
                    result.get('error', 'Failed to update progress'),
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class AudioStatsView(APIView):
    """Get overall audio statistics."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Audio statistics",
        operation_description="Get overall audio availability statistics.",
        tags=['Audio'],
        responses={
            200: openapi.Response(description="Audio statistics"),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request):
        try:
            stats = get_service().get_audio_stats()
            return Response({'status': 'success', 'data': stats}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== SEARCH & UTILITY VIEWS ====================

class SearchVersesView(APIView):
    """Search for verses containing specific text."""
    permission_classes = [AllowAny]

    _MAX_LIMIT = 200

    @swagger_auto_schema(
        operation_summary="Search verses",
        operation_description="Search for verses containing specific text.",
        tags=['Bible'],
        manual_parameters=[
            openapi.Parameter(
                'q', openapi.IN_QUERY,
                description="Search query (required)",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            _LANG_PARAM,
            openapi.Parameter(
                'limit', openapi.IN_QUERY,
                description=f"Maximum results (1–200, default 50)",
                type=openapi.TYPE_INTEGER,
                default=50,
            ),
        ],
        responses={
            200: openapi.Response(description="Search results"),
            400: openapi.Response(description="Missing or invalid parameters", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return _error_response('Search query is required.', status.HTTP_400_BAD_REQUEST)

        # Validate limit before passing to service
        raw_limit = request.query_params.get('limit', '50')
        try:
            limit = int(raw_limit)
            if not (1 <= limit <= self._MAX_LIMIT):
                raise ValueError
        except (ValueError, TypeError):
            return _error_response(
                f"'limit' must be an integer between 1 and {self._MAX_LIMIT}.",
                status.HTTP_400_BAD_REQUEST,
            )

        language = request.query_params.get('language', 'en')
        try:
            results = get_service().search_verses(query, language, limit)
            return Response(
                {
                    'status': 'success',
                    'query': query,
                    'results': results,
                    'total': len(results),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class RandomVerseView(APIView):
    """Get a random Bible verse."""
    permission_classes = [AllowAny]

    _VALID_TESTAMENTS = ('Old', 'New')

    @swagger_auto_schema(
        operation_summary="Random verse",
        operation_description="Get a random Bible verse.",
        tags=['Bible'],
        manual_parameters=[
            _LANG_PARAM,
            openapi.Parameter(
                'testament', openapi.IN_QUERY,
                description="Filter by testament",
                type=openapi.TYPE_STRING,
                enum=['Old', 'New'],
            ),
        ],
        responses={
            200: openapi.Response(description="Random verse"),
            400: openapi.Response(description="Invalid testament value", schema=_ERR_SCHEMA),
            404: openapi.Response(description="No verses found", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request):
        language = request.query_params.get('language', 'en')
        testament = request.query_params.get('testament')

        if testament and testament not in self._VALID_TESTAMENTS:
            return _error_response(
                'testament must be "Old" or "New".', status.HTTP_400_BAD_REQUEST
            )

        try:
            verse = get_service().get_random_verse(language, testament)
            if 'error' in verse:
                # "No verses found" is a 404, not a 500
                return _error_response(verse['error'], status.HTTP_404_NOT_FOUND)
            return Response({'status': 'success', 'data': verse}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerseOfTheDayView(APIView):
    """Get verse of the day."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Verse of the day",
        operation_description="Get the verse of the day based on the current date.",
        tags=['Bible'],
        manual_parameters=[_LANG_PARAM],
        responses={
            200: openapi.Response(description="Verse of the day"),
            404: openapi.Response(description="No verse data available", schema=_ERR_SCHEMA),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request):
        language = request.query_params.get('language', 'en')
        try:
            verse = get_service().get_verse_of_the_day(language)
            if 'error' in verse:
                # Service attaches a 'code' key; fall back to 404 for data issues
                return _service_error_to_response(
                    {**verse, 'code': verse.get('code', 'not_found')}
                )
            return Response({'status': 'success', 'data': verse}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class BibleStatsView(APIView):
    """Get overall Bible statistics."""
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Bible statistics",
        operation_description="Get overall Bible statistics (books, chapters, verses).",
        tags=['Bible'],
        responses={
            200: openapi.Response(description="Bible statistics"),
            500: openapi.Response(description="Server error", schema=_ERR_SCHEMA),
        },
    )
    def get(self, request):
        try:
            stats = get_service().get_bible_stats()
            return Response({'status': 'success', 'data': stats}, status=status.HTTP_200_OK)
        except Exception as e:
            return _error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)