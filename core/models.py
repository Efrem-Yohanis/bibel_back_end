from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.core.validators import MinLengthValidator, MaxLengthValidator

# Custom User Manager
# Custom User Manager - FIXED
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, email=None, **extra_fields):
        if not username:
            raise ValueError('Username is required')
        
        # Normalize email
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
        
        # Don't set is_staff or is_superuser as fields - they are properties
        return self.create_user(username, password, email, **extra_fields)      
# 1. Language table
class Language(models.Model):
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

# 2. Level table (Difficulty levels)
class Level(models.Model):
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

# 3. Testament (Old/New)
class Testament(models.Model):
    name = models.CharField(max_length=50)  # "Old" or "New"
    
    class Meta:
        db_table = 'testaments'
    
    def __str__(self):
        return f"{self.name} Testament"

# 4. Book (Genesis, Exodus, etc.)
class Book(models.Model):
    name = models.CharField(max_length=100)
    testament = models.ForeignKey(Testament, on_delete=models.CASCADE, related_name='books', null=True, blank=True)
    
    class Meta:
        db_table = 'books'
        ordering = ['id']
    
    def __str__(self):
        return self.name

# 5. Chapter
class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.IntegerField()
    
    class Meta:
        db_table = 'chapters'
        unique_together = ['book', 'chapter_number']
        ordering = ['book', 'chapter_number']
    
    def __str__(self):
        return f"{self.book.name} {self.chapter_number}"

# 6. Verse
class Verse(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='verses')
    verse_number = models.IntegerField()
    
    class Meta:
        db_table = 'verses'
        unique_together = ['chapter', 'verse_number']
        ordering = ['chapter', 'verse_number']
    
    def __str__(self):
        return f"{self.chapter.book.name} {self.chapter.chapter_number}:{self.verse_number}"

# 7. Verse Text (Multi-language)
class VerseText(models.Model):
    verse = models.ForeignKey(Verse, on_delete=models.CASCADE, related_name='texts')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='verse_texts')
    text = models.TextField()
    
    class Meta:
        db_table = 'verse_texts'
        unique_together = ['verse', 'language']
    
    def __str__(self):
        return f"{self.verse} - {self.language.code}"

# 8. Question
class Question(models.Model):
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

# 9. Question Text (Multi-language)
class QuestionText(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='texts')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='question_texts')
    text = models.TextField()
    
    class Meta:
        db_table = 'question_texts'
        unique_together = ['question', 'language']
    
    def __str__(self):
        return f"Q{self.question.id} - {self.language.code}"

# 10. Option (A, B, C, D)
class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=1)  # 'A', 'B', 'C', 'D'
    
    class Meta:
        db_table = 'options'
        unique_together = ['question', 'label']
    
    def __str__(self):
        return f"Option {self.label} for Q{self.question.id}"

# 11. Option Text (Multi-language)
class OptionText(models.Model):
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name='texts')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='option_texts')
    text = models.TextField()
    
    class Meta:
        db_table = 'option_texts'
        unique_together = ['option', 'language']
    
    def __str__(self):
        return f"Option {self.option.label} - {self.language.code}"

# 12. Explanation (Multi-language)
class Explanation(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='explanations')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='explanations')
    text = models.TextField()
    
    class Meta:
        db_table = 'explanations'
        unique_together = ['question', 'language']
    
    def __str__(self):
        return f"Explanation Q{self.question.id} - {self.language.code}"

# 13. User (Custom User Model)
# 13. User (Custom User Model) - COMPLETELY FIXED
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True)
    password = models.CharField(max_length=255)  # Django expects 'password'
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
        """Required for admin interface"""
        return self.is_admin
    
    @property
    def is_superuser(self):
        """Required for admin interface"""
        return self.is_admin
    
    # Override required methods
    def has_perm(self, perm, obj=None):
        return self.is_admin
    
    def has_module_perms(self, app_label):
        return self.is_admin



class UserSession(models.Model):
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

# 15. Quiz Attempt
class QuizAttempt(models.Model):
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

# 16. Quiz Answer
class QuizAnswer(models.Model):
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

# 17. User Book Progress
class UserBookProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='book_progress')
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    current_chapter = models.IntegerField(default=1)
    current_verse = models.IntegerField(default=1)
    last_activity = models.DateTimeField(default=timezone.now)
    questions_answered = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_book_progress'
        unique_together = ['user', 'book']
    
    def __str__(self):
        return f"{self.user.username} - {self.book.name}"