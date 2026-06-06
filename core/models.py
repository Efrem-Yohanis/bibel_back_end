# core/models.py
import hashlib
import secrets

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


# ==================== CUSTOM USER MANAGER ====================

class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, email=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')

        if email:
            email = self.normalize_email(email)

        user = self.model(username=username, email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, email=None, **extra_fields):
        # is_superuser comes from PermissionsMixin; is_admin is our app-level flag
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(username, password, email, **extra_fields)


# ==================== BIBLE CONTENT MODELS ====================

class Language(models.Model):
    """Language table for multi-language support"""
    code = models.CharField(max_length=10, unique=True)   # 'en', 'am', 'or', 'ti'
    name = models.CharField(max_length=50)                # 'English', 'Amharic', ...
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
    level_number = models.IntegerField(unique=True)   # 1, 2, 3
    name = models.CharField(max_length=50)            # 'Easy', 'Medium', 'Hard'
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
    testament = models.ForeignKey(
        Testament, on_delete=models.CASCADE,
        related_name='books', null=True, blank=True
    )
    bible_order = models.IntegerField(default=0, help_text="Order in the Bible (1–66)")
    has_audio = models.BooleanField(default=False)
    total_chapters = models.IntegerField(default=0)

    class Meta:
        db_table = 'books'
        ordering = ['bible_order', 'id']

    def __str__(self):
        return self.name

    def get_name(self, language_code='am'):
        entry = self.names.filter(language__code=language_code).first()
        return entry.name if entry else self.name

    def get_all_names(self):
        return {
            bn.language.code: bn.name
            for bn in self.names.select_related('language').all()
        }

    def get_audio_for_language(self, language_code='en'):
        """Get book-level audio for a specific language (single query)."""
        return BookAudio.objects.filter(
            book=self,
            language__code=language_code,
            is_available=True,
        ).first()

    def get_chapter_audio(self, chapter_number, language_code='en'):
        """Get audio for a specific chapter (single query)."""
        return ChapterAudio.objects.filter(
            book=self,
            chapter_number=chapter_number,
            language__code=language_code,
            is_available=True,
        ).first()

    def get_chapter_audio_url(self, chapter_number, language_code='en'):
        chapter_audio = self.get_chapter_audio(chapter_number, language_code)
        return chapter_audio.get_audio_url() if chapter_audio else None


class BookName(models.Model):
    """Multi-language book names"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='names')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='book_names')
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'book_names'
        unique_together = ['book', 'language']
        ordering = ['book__bible_order']

    def __str__(self):
        return f"{self.language.code}: {self.name}"


class Chapter(models.Model):
    """Bible chapter model"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.IntegerField()
    total_verses = models.IntegerField(default=0)

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

class AudioMixin(models.Model):
    """
    Abstract mixin that provides shared audio URL resolution logic for
    BookAudio and ChapterAudio, eliminating duplicated code.
    """
    audio_url = models.URLField(max_length=500, blank=True, null=True)
    cloudinary_public_id = models.CharField(max_length=500, blank=True, null=True)
    duration = models.IntegerField(help_text="Duration in seconds", null=True, blank=True)
    file_size = models.BigIntegerField(help_text="File size in bytes", null=True, blank=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def get_audio_url(self):
        if self.audio_url:
            return self.audio_url
        if self.cloudinary_public_id:
            try:
                from cloudinary.utils import cloudinary_url
                public_id = str(self.cloudinary_public_id)
                for resource_type in ('video', 'raw', 'auto'):
                    try:
                        url, _ = cloudinary_url(
                            public_id, resource_type=resource_type,
                            secure=True, sign=True
                        )
                        if url:
                            return url
                    except Exception:
                        continue
            except Exception:
                return None
        return None


class BookAudio(AudioMixin):
    """Audio files for entire Bible books (for continuous play)"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='audio')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='book_audios')

    part_number = models.IntegerField(default=1, help_text="Part number for multi-part books")
    total_parts = models.IntegerField(default=1, help_text="Total parts for multi-part books")
    chapter_timestamps = models.JSONField(
        default=dict,
        help_text="Mapping of chapter numbers to timestamps in seconds"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'book_audios'
        unique_together = ['book', 'language', 'part_number']
        ordering = ['book', 'part_number']

    def __str__(self):
        part_info = f" (Part {self.part_number}/{self.total_parts})" if self.total_parts > 1 else ""
        return f"{self.book.name} - {self.language.code}{part_info}"

    def get_chapter_start_time(self, chapter_number):
        return self.chapter_timestamps.get(str(chapter_number), 0)


class ChapterAudio(AudioMixin):
    """Audio files for individual chapters"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapter_audios')
    # Single FK to Chapter is sufficient; chapter_number is derived via chapter__chapter_number.
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE,
        related_name='audio', null=True, blank=True
    )
    # Denormalised for query convenience — kept intentionally and documented here.
    # Must always equal chapter.chapter_number; enforced in save().
    chapter_number = models.IntegerField(db_index=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='chapter_audios')

    start_time = models.IntegerField(default=0, help_text="Start time in seconds within full-book audio")
    end_time = models.IntegerField(null=True, blank=True, help_text="End time in seconds within full-book audio")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chapter_audios'
        unique_together = ['book', 'chapter_number', 'language']
        ordering = ['book', 'chapter_number']

    def __str__(self):
        return f"{self.book.name} Chapter {self.chapter_number} - {self.language.code}"

    def save(self, *args, **kwargs):
        # Keep denormalised field in sync with the FK
        if self.chapter_id and self.chapter.chapter_number != self.chapter_number:
            self.chapter_number = self.chapter.chapter_number
        super().save(*args, **kwargs)


# ==================== QUIZ MODELS ====================

class Question(models.Model):
    """Quiz question model"""
    OPTION_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]

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
    label = models.CharField(max_length=1)

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
    """
    Custom User Model.

    PermissionsMixin already provides is_superuser (a real DB field), has_perm,
    and has_module_perms — we do NOT override those.  is_admin is our own
    application-level admin flag; is_staff is derived from it so Django's
    built-in admin site works correctly.
    """
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    # email is optional at the model level; remove from REQUIRED_FIELDS to match.
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=255, blank=True, null=True)
    reset_token_expires = models.DateTimeField(blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=255, blank=True, null=True)
    email_verification_token_expires = models.DateTimeField(blank=True, null=True)
    preferred_language = models.ForeignKey(
        Language, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users'
    )

    total_quizzes_taken = models.IntegerField(default=0)
    total_correct_answers = models.IntegerField(default=0)
    total_questions_answered = models.IntegerField(default=0)

    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    auth_provider = models.CharField(max_length=50, blank=True, null=True)

    USERNAME_FIELD = 'username'
    # email is nullable, so it must not appear in REQUIRED_FIELDS
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        ordering = ['username']

    def __str__(self):
        return self.username

    @property
    def is_staff(self):
        """Required by Django admin; mirrors is_admin."""
        return self.is_admin


class UserSession(models.Model):
    """
    User session for token authentication.

    Only a SHA-256 hash of the raw token is stored so a database leak does
    not expose active sessions.  Use UserSession.create_for_user() to
    generate a session and obtain the one-time plaintext token.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    # Stores SHA-256(raw_token) — never the raw token itself.
    # null=True only to allow the schema migration to run on existing rows;
    # all pre-existing rows are deleted by the data migration that follows,
    # so in practice this column is always populated at runtime.
    token_hash = models.CharField(max_length=64, unique=True, null=True)
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

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()

    @classmethod
    def create_for_user(cls, user, expires_at, **kwargs):
        """
        Generate a cryptographically secure token, persist only its hash,
        and return (session, raw_token).  The caller must deliver raw_token
        to the client; it cannot be recovered later.
        """
        raw_token = secrets.token_urlsafe(32)
        session = cls.objects.create(
            user=user,
            token_hash=cls.hash_token(raw_token),
            expires_at=expires_at,
            **kwargs,
        )
        return session, raw_token

    @classmethod
    def get_by_raw_token(cls, raw_token: str):
        """Look up an active session from a plaintext token."""
        try:
            return cls.objects.get(
                token_hash=cls.hash_token(raw_token),
                is_active=True,
            )
        except cls.DoesNotExist:
            return None


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
    # Changed from TextField — JSONField provides type safety and avoids manual parsing.
    resume_data = models.JSONField(blank=True, null=True)

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

    audio_current_position = models.IntegerField(default=0, help_text="Current position in seconds")
    audio_completed_chapters = models.JSONField(default=list, help_text="Chapter numbers completed via audio")
    last_audio_listened = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'user_book_progress'
        unique_together = ['user', 'book']

    def __str__(self):
        return f"{self.user.username} - {self.book.name}"

    def get_audio_progress_percentage(self):
        if self.book.total_chapters > 0:
            return int((len(self.audio_completed_chapters) / self.book.total_chapters) * 100)
        return 0

    def get_chapter_audio_progress(self, chapter_number):
        """
        Return audio progress info for a specific chapter.
        Moved here from Book, where it did not belong — progress is
        always user-specific and needs a UserBookProgress instance.
        """
        chapter_audio = self.book.get_chapter_audio(chapter_number)
        if chapter_audio:
            return {
                'has_audio': True,
                'duration': chapter_audio.duration,
                'url': chapter_audio.get_audio_url(),
                'start_time': chapter_audio.start_time,
            }
        return {'has_audio': False}


# ==================== DAILY VERSE MODELS ====================

class DailyVerseCategory(models.Model):
    """Category for daily verse selection"""
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, help_text="URL-friendly identifier")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'daily_verse_categories'
        ordering = ['title']
        verbose_name_plural = 'Daily Verse Categories'

    def __str__(self):
        return self.title


class DailyVerse(models.Model):
    """
    Pre-selected daily verses from curated list (1 000 verses across 11 categories).

    unique_together = ['category', 'verse'] allows the same verse to appear in
    multiple categories intentionally (e.g. John 3:16 in both 'Salvation' and
    'Love').  If global uniqueness per verse is ever required, add a
    UniqueConstraint on verse alone.
    """
    category = models.ForeignKey(DailyVerseCategory, on_delete=models.CASCADE, related_name='verses')
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name='daily_verse_entries')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'daily_verses'
        unique_together = ['category', 'verse']
        ordering = ['category', 'id']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['verse']),
        ]

    def __str__(self):
        return f"{self.verse} - {self.category.title}"