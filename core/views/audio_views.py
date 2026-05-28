"""Audio progress API views"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..services.bible_service import BibleService

bible_service = BibleService()


class RecordChapterCompletionView(APIView):
    """Record that user completed a chapter audio"""
    permission_classes = [IsAuthenticated]

    def post(self, request, book_id, chapter_number):
        language = request.query_params.get('language', 'en')

        result = bible_service.record_chapter_completion(
            user_id=request.user.id,
            book_id=book_id,
            chapter_number=chapter_number,
            language_code=language
        )

        if result.get('success'):
            return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)

        return Response({'status': 'error', 'message': result.get('error')}, status=status.HTTP_400_BAD_REQUEST)


class UserAudioProgressView(APIView):
    """Get user's audio progress for a book"""
    permission_classes = [IsAuthenticated]

    def get(self, request, book_id):
        result = bible_service.get_user_audio_status(request.user.id, book_id)
        return Response({'status': 'success', 'data': result}, status=status.HTTP_200_OK)
