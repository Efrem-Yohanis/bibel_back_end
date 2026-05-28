# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator

# ==================== CUSTOM USER MANAGER ====================

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, email=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        
        if email:
            email = self.normalize_email(email)
        
        user = self.model(
            username=username,
            email=email,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password=None, email=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(username, password, email, **extra_fields)


# ==================== BIBLE CONTENT MODELS ====================

class Language(models.Model):
    """Language table for multi-language support"""
    code = models.CharField(max_length=10, unique=True)  # 'en', 'am', 'or', 'ti'
    name = models.CharField(max_length=50)  # 'English', 'Amharic', 'Afaan Oromo', 'Tigrinya'
    native_name = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'languages'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Level(models.Model):
    """Difficulty levels for quizzes"""
    level_number = models.IntegerField(unique=True)  # 1, 2, 3
    name = models.CharField(max_length=50)  # 'Easy', 'Medium', 'Hard'
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'levels'
        ordering = ['level_number']
    
    def __str__(self):
        return f"Level {self.level_number}: {self.name}"


class Testament(models.Model):
    """Old or New Testament"""
    name = models.CharField(max_length=50)  # "Old" or "New"
    
    class Meta:
        db_table = 'testaments'
    
    def __str__(self):
        return f"{self.name} Testament"


class Book(models.Model):
    """Bible book model with audio support"""
    name = models.CharField(max_length=100)
    testament = models.ForeignKey(Testament, on_delete=models.CASCADE, related_name='books', null=True, blank=True)
    
    # New audio-related fields
    bible_order = models.IntegerField(default=0, help_text="Order in the Bible (1-66)")
    has_audio = models.BooleanField(default=False, help_text="Whether audio is available for this book")
    total_chapters = models.IntegerField(default=0, help_text="Total number of chapters")
    
    
    class Meta:
        db_table = 'books'
        ordering = ['bible_order', 'id']
    
    def __str__(self):
        return self.name
    
    def get_audio_for_language(self, language_code='en'):
        """Get book-level audio for a specific language"""
        try:
            language = Language.objects.get(code=language_code)
            return BookAudio.objects.filter(
                book=self, 
                language=language, 
                is_available=True
            ).first()
        except Language.DoesNotExist:
            return None
    
    def get_chapter_audio(self, chapter_number, language_code='en'):
        """Get audio for a specific chapter"""
        try:
            language = Language.objects.get(code=language_code)
            return ChapterAudio.objects.get(
                book=self,
                chapter_number=chapter_number,
                language=language,
                is_available=True
            )
        except (ChapterAudio.DoesNotExist, Language.DoesNotExist):
            return None
    
    def get_chapter_audio_url(self, chapter_number, language_code='en'):
        """Get audio URL for a specific chapter"""
        chapter_audio = self.get_chapter_audio(chapter_number, language_code)
        return chapter_audio.get_audio_url() if chapter_audio else None
    
    def get_audio_progress(self, chapter_number, language_code='en'):
        """Get audio progress for a specific chapter"""
        chapter_audio = self.get_chapter_audio(chapter_number, language_code)
        if chapter_audio:
            return {
                'has_audio': True,
                'duration': chapter_audio.duration,
                'url': chapter_audio.get_audio_url(),
                'start_time': chapter_audio.start_time
            }
        return {'has_audio': False}


class Chapter(models.Model):
    """Bible chapter model"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.IntegerField()
    total_verses = models.IntegerField(default=0, help_text="Total number of verses in this chapter")
    
    class Meta:
        db_table = 'chapters'
        unique_together = ['book', 'chapter_number']
        ordering = ['book', 'chapter_number']
    
    def __str__(self):
        return f"{self.book.name} {self.chapter_number}"


class Verse(models.Model):
    """Bible verse model"""
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='verses')
    verse_number = models.IntegerField()
    
    class Meta:
        db_table = 'verses'
        unique_together = ['chapter', 'verse_number']
        ordering = ['chapter', 'verse_number']
    
    def __str__(self):
        return f"{self.chapter.book.name} {self.chapter.chapter_number}:{self.verse_number}"


class VerseText(models.Model):
    """Multi-language verse text"""
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name='texts')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='verse_texts')
    text = models.TextField()
    
    class Meta:
        db_table = 'verse_texts'
        unique_together = ['verse', 'language']
    
    def __str__(self):
        return f"{self.verse} - {self.language.code}"


# ==================== AUDIO MODELS ====================

class BookAudio(models.Model):
    """Audio files for entire Bible books (for continuous play)"""
    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name='audio')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='book_audios')
    
    # Audio file information
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    cloudinary_public_id = models.CharField(max_length=500, blank=True, null=True)
    
    # Audio metadata
    duration = models.IntegerField(help_text="Duration in seconds", null=True, blank=True)
    file_size = models.BigIntegerField(help_text="File size in bytes", null=True, blank=True)
    is_available = models.BooleanField(default=True)
    
    # For multi-part books (Psalms has 3 parts, Isaiah has 2, etc.)
    part_number = models.IntegerField(default=1, help_text="Part number for multi-part books")
    total_parts = models.IntegerField(default=1, help_text="Total parts for multi-part books")
    
    # Chapter timestamps for navigation
    chapter_timestamps = models.JSONField(default=dict, help_text="Mapping of chapter numbers to timestamps in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'book_audios'
        unique_together = ['book', 'language', 'part_number']
        ordering = ['book', 'part_number']
    
    def __str__(self):
        part_info = f" (Part {self.part_number}/{self.total_parts})" if self.total_parts > 1 else ""
        return f"{self.book.name} - {self.language.code}{part_info}"
    
    def get_audio_url(self):
        """Get the full audio URL"""
        return self.audio_url if self.audio_url else None
    
    def get_chapter_start_time(self, chapter_number):
        """Get start time for a specific chapter"""
        return self.chapter_timestamps.get(str(chapter_number), 0)


class ChapterAudio(models.Model):
    """Audio files for individual chapters (granular control)"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapter_audios')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='audio', null=True, blank=True)
    chapter_number = models.IntegerField()  # Denormalized for easier querying
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='chapter_audios')
    
    # Audio file information
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    cloudinary_public_id = models.CharField(max_length=500, blank=True, null=True)
    
    # Audio metadata
    duration = models.IntegerField(help_text="Duration in seconds", null=True, blank=True)
    file_size = models.BigIntegerField(help_text="File size in bytes", null=True, blank=True)
    is_available = models.BooleanField(default=True)
    
    # For continuous play across chapters
    start_time = models.IntegerField(default=0, help_text="Start time in seconds for full book audio")
    end_time = models.IntegerField(null=True, blank=True, help_text="End time in seconds for full book audio")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chapter_audios'
        unique_together = ['book', 'chapter_number', 'language']
        ordering = ['book', 'chapter_number']
    
    def __str__(self):
        return f"{self.book.name} Chapter {self.chapter_number} - {self.language.code}"
    
    def get_audio_url(self):
        """Get the full audio URL"""
        return self.audio_url if self.audio_url else None


# ==================== QUIZ MODELS ====================

class Question(models.Model):
    """Quiz question model"""
    OPTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='questions', null=True, blank=True)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    verse_reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'questions'
        ordering = ['id']
    
    def __str__(self):
        return f"Question {self.id} - {self.book.name if self.book else 'No book'}"


class QuestionText(models.Model):
    """Multi-language question text"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='texts')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='question_texts')
    text = models.TextField()
    
    class Meta:
        db_table = 'question_texts'
        unique_together = ['question', 'language']
    
    def __str__(self):
        return f"Q{self.question.id} - {self.language.code}"


class Option(models.Model):
    """Quiz options (A, B, C, D)"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=1)  # 'A', 'B', 'C', 'D'
    
    class Meta:
        db_table = 'options'
        unique_together = ['question', 'label']
    
    def __str__(self):
        return f"Option {self.label} for Q{self.question.id}"


class OptionText(models.Model):
    """Multi-language option text"""
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='texts')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='option_texts')
    text = models.TextField()
    
    class Meta:
        db_table = 'option_texts'
        unique_together = ['option', 'language']
    
    def __str__(self):
        return f"Option {self.option.label} - {self.language.code}"


class Explanation(models.Model):
    """Multi-language answer explanation"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='explanations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='explanations')
    text = models.TextField()
    
    class Meta:
        db_table = 'explanations'
        unique_together = ['question', 'language']
    
    def __str__(self):
        return f"Explanation Q{self.question.id} - {self.language.code}"


# ==================== USER MODELS ====================

class User(AbstractBaseUser, PermissionsMixin):
    """Custom User Model"""
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=255, blank=True, null=True)
    reset_token_expires = models.DateTimeField(blank=True, null=True)
    preferred_language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    # Statistics
    total_quizzes_taken = models.IntegerField(default=0)
    total_correct_answers = models.IntegerField(default=0)
    total_questions_answered = models.IntegerField(default=0)
    
    # Google Auth fields
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    auth_provider = models.CharField(max_length=50, blank=True, null=True)
    
    # Django requirements
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    objects = CustomUserManager()
    
    class Meta:
        db_table = 'users'
        ordering = ['username']
    
    def __str__(self):
        return self.username
    
    @property
    def is_staff(self):
        return self.is_admin
    
    @property
    def is_superuser(self):
        return self.is_admin
    
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return self.is_admin


class UserSession(models.Model):
    """User session for token authentication"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_sessions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session for {self.user.username}"


class QuizAttempt(models.Model):
    """Quiz attempt tracking"""
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quiz_attempts')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='quiz_attempts', null=True, blank=True)
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='quiz_attempts', null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='quiz_attempts', null=True, blank=True)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    score_percentage = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
    resume_data = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Attempt {self.id} - {self.user.username}"


class QuizAnswer(models.Model):
    """Individual quiz answers"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'quiz_answers'
        ordering = ['answered_at']
    
    def __str__(self):
        return f"Answer for Q{self.question.id} - {'Correct' if self.is_correct else 'Wrong'}"


class UserBookProgress(models.Model):
    """Track user's progress through books (reading + audio)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_progress')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    current_chapter = models.IntegerField(default=1)
    current_verse = models.IntegerField(default=1)
    last_activity = models.DateTimeField(default=timezone.now)
    questions_answered = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    
    # Audio-specific progress
    audio_current_position = models.IntegerField(default=0, help_text="Current position in seconds")
    audio_completed_chapters = models.JSONField(default=list, help_text="Chapters completed via audio")
    last_audio_listened = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'user_book_progress'
        unique_together = ['user', 'book']
    
    def __str__(self):
        return f"{self.user.username} - {self.book.name}"
    
    def get_audio_progress_percentage(self):
        """Get audio progress percentage for the current book"""
        if self.book.total_chapters > 0:
            return int((len(self.audio_completed_chapters) / self.book.total_chapters) * 100)
        return 0