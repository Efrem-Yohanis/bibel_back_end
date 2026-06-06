# core/serializers/book_serializers.py
from rest_framework import serializers
from ..models import Book, Testament, Language, BookAudio, ChapterAudio, UserBookProgress


# ==================== HELPERS ====================

def _get_language_code(context: dict) -> str:
    """
    Resolve the requested language code from serializer context.
    Falls back to 'en' when absent or malformed.
    """
    request = context.get('request')
    if request and hasattr(request, 'query_params'):
        return request.query_params.get('language', 'en')
    return 'en'


def _build_audio_payload(obj: Book, language_code: str) -> dict | None:
    """
    Single, reusable audio resolver for a Book + language pair.
    Queries book-level audio first; falls back to chapter-level audio.
    Returns None when no audio is available.

    Avoids the extra Language.objects.get() by filtering on language__code.
    """
    # --- Full-book audio ---
    book_audio = (
        BookAudio.objects
        .filter(book=obj, language__code=language_code, is_available=True)
        .select_related('language')
        .first()
    )
    if book_audio:
        return {
            'type': 'full_book',
            'audio_url': book_audio.get_audio_url(),
            'duration': book_audio.duration,
            'part_number': book_audio.part_number,
            'total_parts': book_audio.total_parts,
            'chapter_timestamps': book_audio.chapter_timestamps,
        }

    # --- Chapter-by-chapter audio ---
    chapter_audios = (
        ChapterAudio.objects
        .filter(book=obj, language__code=language_code, is_available=True)
        .order_by('chapter_number')
    )
    if chapter_audios.exists():
        return {
            'type': 'chapter_by_chapter',
            'total_chapters_with_audio': chapter_audios.count(),
            'chapters': [
                {
                    'chapter': ca.chapter_number,
                    'audio_url': ca.get_audio_url(),
                    'duration': ca.duration,
                }
                for ca in chapter_audios
            ],
        }

    return None


def _build_audio_summary(obj: Book, language_code: str) -> dict | None:
    """
    Lightweight audio check (no per-chapter detail) used in
    BookWithChaptersSerializer.get_audio and similar contexts.
    """
    book_audio = (
        BookAudio.objects
        .filter(book=obj, language__code=language_code, is_available=True)
        .first()
    )
    if book_audio:
        return {
            'type': 'full_book',
            'audio_url': book_audio.get_audio_url(),
            'duration': book_audio.duration,
        }

    if ChapterAudio.objects.filter(
        book=obj, language__code=language_code, is_available=True
    ).exists():
        return {'type': 'chapter_by_chapter', 'available': True}

    return None


# ==================== TESTAMENT SERIALIZER ====================

class TestamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testament
        fields = ['id', 'name']


# ==================== AUDIO SERIALIZERS ====================

class BookAudioSerializer(serializers.ModelSerializer):
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    duration_formatted = serializers.SerializerMethodField()

    class Meta:
        model = BookAudio
        fields = [
            'id', 'audio_url', 'duration', 'duration_formatted',
            'file_size', 'is_available', 'part_number', 'total_parts',
            'language_code', 'language_name', 'chapter_timestamps',
        ]

    def get_duration_formatted(self, obj) -> str | None:
        if obj.duration:
            minutes, seconds = divmod(obj.duration, 60)
            return f"{minutes}:{seconds:02d}"
        return None


class ChapterAudioInfoSerializer(serializers.ModelSerializer):
    """Simplified ChapterAudio representation for book views."""
    class Meta:
        model = ChapterAudio
        fields = ['chapter_number', 'audio_url', 'duration', 'is_available']


# ==================== BOOK SERIALIZERS ====================

class BookListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for book list endpoints.

    chapter_count uses the denormalised total_chapters field — no extra
    query per row.  If you need the live DB count, annotate the queryset
    in the view instead of calling .count() here.
    """
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    # Expose total_chapters directly; avoid an extra .count() query per row.
    chapter_count = serializers.IntegerField(source='total_chapters', read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'testament', 'testament_name',
            'bible_order', 'has_audio', 'total_chapters', 'chapter_count',
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """Detailed Book serializer with audio information."""
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    chapter_count = serializers.IntegerField(source='total_chapters', read_only=True)
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'testament', 'testament_name',
            'bible_order', 'has_audio', 'total_chapters', 'chapter_count', 'audio',
        ]

    def get_audio(self, obj) -> dict | None:
        return _build_audio_payload(obj, _get_language_code(self.context))


class BookWithChaptersSerializer(serializers.ModelSerializer):
    """
    Book serializer that includes per-chapter detail.

    To avoid N+1 queries on has_audio, prefetch chapter audio in the view:

        queryset = Book.objects.prefetch_related(
            'chapters__verses__texts',
            Prefetch(
                'chapter_audios',
                queryset=ChapterAudio.objects.filter(
                    language__code=language_code, is_available=True
                ),
                to_attr='prefetched_chapter_audios',
            ),
        )

    When that prefetch is present the serializer uses it; otherwise it
    falls back to per-chapter queries (still correct, just slower).
    """
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    chapters = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'testament', 'testament_name',
            'bible_order', 'has_audio', 'total_chapters',
            'chapters', 'audio',
        ]

    def get_chapters(self, obj) -> list:
        language_code = _get_language_code(self.context)

        # Use prefetched audio when available to avoid N+1 queries.
        prefetched = getattr(obj, 'prefetched_chapter_audios', None)
        if prefetched is not None:
            audio_chapter_numbers = {ca.chapter_number for ca in prefetched}
        else:
            audio_chapter_numbers = set(
                ChapterAudio.objects
                .filter(book=obj, language__code=language_code, is_available=True)
                .values_list('chapter_number', flat=True)
            )

        result = []
        for chapter in obj.chapters.all().order_by('chapter_number'):
            verse_count = chapter.verses.filter(
                texts__language__code=language_code
            ).count()
            result.append({
                'chapter_number': chapter.chapter_number,
                'total_verses': verse_count,
                'has_audio': chapter.chapter_number in audio_chapter_numbers,
            })
        return result

    def get_audio(self, obj) -> dict | None:
        return _build_audio_summary(obj, _get_language_code(self.context))


class BookAudioOnlySerializer(serializers.ModelSerializer):
    """Minimal Book serializer for audio-only endpoints."""
    testament_name = serializers.CharField(source='testament.name', read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'name', 'testament_name', 'has_audio', 'bible_order']


class BookProgressSerializer(serializers.ModelSerializer):
    """
    Book serializer with user progress information.

    Avoids repeated UserBookProgress queries by expecting the view to
    pass a pre-fetched progress map via context:

        progress_map = {
            p.book_id: p
            for p in UserBookProgress.objects.filter(
                user=request.user,
                book__in=queryset,
            )
        }
        serializer = BookProgressSerializer(
            queryset, many=True,
            context={'request': request, 'progress_map': progress_map},
        )
    """
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    audio_progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'name', 'testament_name', 'bible_order',
            'has_audio', 'total_chapters',
            'progress_percentage', 'audio_progress_percentage',
        ]

    def _get_progress(self, obj) -> UserBookProgress | None:
        """Return the UserBookProgress for this book from context or DB."""
        user = self.context.get('user')
        if not (user and user.is_authenticated):
            return None

        # Prefer pre-fetched map to avoid per-book queries.
        progress_map = self.context.get('progress_map')
        if progress_map is not None:
            return progress_map.get(obj.pk)

        # Fallback: single query (acceptable when serializing one book).
        try:
            return UserBookProgress.objects.get(user=user, book=obj)
        except UserBookProgress.DoesNotExist:
            return None

    def get_progress_percentage(self, obj) -> int:
        progress = self._get_progress(obj)
        if progress and obj.total_chapters > 0:
            return int((progress.current_chapter / obj.total_chapters) * 100)
        return 0

    def get_audio_progress_percentage(self, obj) -> int:
        if not obj.has_audio:
            return 0
        progress = self._get_progress(obj)
        if progress and obj.total_chapters > 0:
            completed = len(progress.audio_completed_chapters)
            return int((completed / obj.total_chapters) * 100)
        return 0