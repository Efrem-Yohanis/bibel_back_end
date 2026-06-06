# core/serializers/book_serializers.py
from rest_framework import serializers
from ..models import Book, Testament, Language, BookAudio, ChapterAudio


# ==================== TESTAMENT SERIALIZER ====================

class TestamentSerializer(serializers.ModelSerializer):
    """Serializer for Testament model"""
    class Meta:
        model = Testament
        fields = ['id', 'name']


# ==================== BOOK AUDIO SERIALIZER ====================

class BookAudioSerializer(serializers.ModelSerializer):
    """Serializer for BookAudio model"""
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name', read_only=True)
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = BookAudio
        fields = [
            'id', 'audio_url', 'duration', 'duration_formatted', 
            'file_size', 'is_available', 'part_number', 'total_parts',
            'language_code', 'language_name', 'chapter_timestamps'
        ]
    
    def get_duration_formatted(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}:{seconds:02d}"
        return None


class ChapterAudioInfoSerializer(serializers.ModelSerializer):
    """Serializer for ChapterAudio (simplified for book view)"""
    class Meta:
        model = ChapterAudio
        fields = ['chapter_number', 'audio_url', 'duration', 'is_available']


# ==================== BOOK SERIALIZERS ====================
# core/serializers/book_serializers.py


class BookListSerializer(serializers.ModelSerializer):
    """Simplified Book serializer for lists"""
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    # Use a different name for annotated fields
    chapter_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Book
        fields = [
            'id', 'name', 'testament', 'testament_name', 
            'bible_order', 'has_audio', 'total_chapters', 'chapter_count'
        ]
    
    def get_chapter_count(self, obj):
        """Get actual chapter count from database"""
        return obj.chapters.count()


class BookDetailSerializer(serializers.ModelSerializer):
    """Detailed Book serializer with audio information"""
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    chapter_count = serializers.SerializerMethodField(read_only=True)
    audio = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'name', 'testament', 'testament_name', 
            'bible_order', 'has_audio', 'total_chapters', 'chapter_count', 'audio'
        ]
    
    def get_chapter_count(self, obj):
        """Get actual chapter count from database"""
        return obj.chapters.count()
    
    def get_audio(self, obj):
        """Get audio information for this book in the requested language"""
        request = self.context.get('request')
        language_code = 'en'
        
        if request and hasattr(request, 'query_params'):
            language_code = request.query_params.get('language', 'en')
        
        try:
            language = Language.objects.get(code=language_code)
            
            # Check for book-level audio first
            book_audio = BookAudio.objects.filter(
                book=obj, 
                language=language, 
                is_available=True
            ).first()
            
            if book_audio:
                return {
                    'type': 'full_book',
                    'audio_url': book_audio.get_audio_url(),
                    'duration': book_audio.duration,
                    'part_number': book_audio.part_number,
                    'total_parts': book_audio.total_parts,
                    'chapter_timestamps': book_audio.chapter_timestamps
                }
            
            # Check for chapter-level audio
            chapter_audios = ChapterAudio.objects.filter(
                book=obj,
                language=language,
                is_available=True
            ).order_by('chapter_number')
            
            if chapter_audios.exists():
                return {
                    'type': 'chapter_by_chapter',
                    'total_chapters_with_audio': chapter_audios.count(),
                    'chapters': [
                        {
                            'chapter': ca.chapter_number,
                            'audio_url': ca.get_audio_url(),
                            'duration': ca.duration
                        }
                        for ca in chapter_audios
                    ]
                }
            
        except Language.DoesNotExist:
            pass
        
        return None
class BookWithChaptersSerializer(serializers.ModelSerializer):
    """Book serializer including chapter list"""
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    chapters = serializers.SerializerMethodField()
    audio = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'name', 'testament', 'testament_name', 
            'bible_order', 'has_audio', 'total_chapters', 
            'chapters', 'audio'
        ]
    
    def get_chapters(self, obj):
        """Get list of chapters with their verse counts"""
        request = self.context.get('request')
        language_code = 'en'
        
        if request and hasattr(request, 'query_params'):
            language_code = request.query_params.get('language', 'en')
        
        try:
            language = Language.objects.get(code=language_code)
            
            chapters = []
            for chapter in obj.chapters.all().order_by('chapter_number'):
                # Count verses available in this language
                verse_count = chapter.verses.filter(
                    texts__language=language
                ).count()
                
                # Check if audio available for this chapter
                has_audio = ChapterAudio.objects.filter(
                    book=obj,
                    chapter_number=chapter.chapter_number,
                    language=language,
                    is_available=True
                ).exists()
                
                chapters.append({
                    'chapter_number': chapter.chapter_number,
                    'total_verses': verse_count,
                    'has_audio': has_audio
                })
            
            return chapters
        except Language.DoesNotExist:
            return []
    
    def get_audio(self, obj):
        """Get audio information for the book"""
        request = self.context.get('request')
        language_code = 'en'
        
        if request and hasattr(request, 'query_params'):
            language_code = request.query_params.get('language', 'en')
        
        try:
            language = Language.objects.get(code=language_code)
            book_audio = BookAudio.objects.filter(
                book=obj, 
                language=language, 
                is_available=True
            ).first()
            
            if book_audio:
                return {
                    'type': 'full_book',
                    'audio_url': book_audio.get_audio_url(),
                    'duration': book_audio.duration
                }

            chapter_audio_exists = ChapterAudio.objects.filter(
                book=obj,
                language=language,
                is_available=True
            ).exists()

            if chapter_audio_exists:
                return {'type': 'chapter_by_chapter', 'available': True}

            return None
        except:
            return None


class BookAudioOnlySerializer(serializers.ModelSerializer):
    """Minimal Book serializer for audio endpoints"""
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    
    class Meta:
        model = Book
        fields = ['id', 'name', 'testament_name', 'has_audio', 'bible_order']


class BookProgressSerializer(serializers.ModelSerializer):
    """Book serializer with user progress information"""
    testament_name = serializers.CharField(source='testament.name', read_only=True)
    progress_percentage = serializers.SerializerMethodField()
    audio_progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Book
        fields = [
            'id', 'name', 'testament_name', 'bible_order', 
            'has_audio', 'total_chapters', 'progress_percentage', 
            'audio_progress_percentage'
        ]
    
    def get_progress_percentage(self, obj):
        """Get user's reading progress for this book"""
        user = self.context.get('user')
        if user and user.is_authenticated:
            from ..models import UserBookProgress
            try:
                progress = UserBookProgress.objects.get(user=user, book=obj)
                if obj.total_chapters > 0:
                    return int((progress.current_chapter / obj.total_chapters) * 100)
            except UserBookProgress.DoesNotExist:
                pass
        return 0
    
    def get_audio_progress_percentage(self, obj):
        """Get user's audio progress for this book"""
        user = self.context.get('user')
        if user and user.is_authenticated and obj.has_audio:
            from ..models import UserBookProgress
            try:
                progress = UserBookProgress.objects.get(user=user, book=obj)
                completed = len(progress.audio_completed_chapters)
                if obj.total_chapters > 0:
                    return int((completed / obj.total_chapters) * 100)
            except UserBookProgress.DoesNotExist:
                pass
        return 0