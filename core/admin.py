# core/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import *

# ==================== EXISTING ADMIN CLASSES (ENHANCED) ====================

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'native_name', 'is_active', 'created_at']
    search_fields = ['code', 'name']
    list_filter = ['is_active']
    list_editable = ['is_active']
    ordering = ['code']


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['level_number', 'name', 'icon', 'color', 'description_preview']
    search_fields = ['name', 'description']
    list_editable = ['name', 'icon', 'color']
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'


@admin.register(Testament)
class TestamentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'book_count']
    search_fields = ['name']
    
    def book_count(self, obj):
        return obj.books.count()
    book_count.short_description = 'Books'


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['name', 'testament', 'bible_order', 'has_audio', 'total_chapters', 'audio_status', 'chapter_count']
    list_filter = ['testament', 'has_audio']
    search_fields = ['name']
    list_editable = ['bible_order', 'has_audio', 'total_chapters']
    ordering = ['bible_order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'testament')
        }),
        ('Ordering', {
            'fields': ('bible_order',)
        }),
        ('Audio Information', {
            'fields': ('has_audio', 'total_chapters'),
            'classes': ('collapse',)
        }),
    )
    
    def audio_status(self, obj):
        if obj.has_audio:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Available</span>')
        return format_html('<span style="color: #dc3545; font-weight: bold;">✗ Not Available</span>')
    audio_status.short_description = 'Audio'
    
    def chapter_count(self, obj):
        return obj.chapters.count()
    chapter_count.short_description = 'Chapters'


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['book', 'chapter_number', 'total_verses', 'verse_count', 'has_audio']
    list_filter = ['book']
    search_fields = ['book__name']
    list_editable = ['total_verses']
    
    def verse_count(self, obj):
        return obj.verses.count()
    verse_count.short_description = 'Verses'
    
    def has_audio(self, obj):
        audio_exists = ChapterAudio.objects.filter(book=obj.book, chapter_number=obj.chapter_number, is_available=True).exists()
        if audio_exists:
            return format_html('<span style="color: #28a745;">✓</span>')
        return format_html('<span style="color: #dc3545;">✗</span>')
    has_audio.short_description = 'Audio'


@admin.register(Verse)
class VerseAdmin(admin.ModelAdmin):
    list_display = ['chapter', 'verse_number', 'has_text']
    list_filter = ['chapter__book', 'chapter']
    search_fields = ['chapter__book__name']
    
    def has_text(self, obj):
        return obj.texts.exists()
    has_text.boolean = True
    has_text.short_description = 'Has Text'


@admin.register(VerseText)
class VerseTextAdmin(admin.ModelAdmin):
    list_display = ['verse', 'language', 'text_preview']
    list_filter = ['language', 'verse__chapter__book']
    search_fields = ['verse__chapter__book__name', 'text']
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Text'


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_active', 'is_admin', 'created_at', 'total_quizzes_taken']
    list_filter = ['is_active', 'is_admin']
    search_fields = ['username', 'email']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('username', 'email', 'password')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_admin')
        }),
        ('Statistics', {
            'fields': ('total_quizzes_taken', 'total_correct_answers', 'total_questions_answered'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )


# ==================== NEW AUDIO MODEL ADMINS ====================

@admin.register(BookAudio)
class BookAudioAdmin(admin.ModelAdmin):
    list_display = ['book', 'language', 'part_display', 'duration_formatted', 'is_available', 'file_size_kb']
    list_filter = ['language', 'is_available', 'total_parts']
    search_fields = ['book__name', 'language__name']
    list_editable = ['is_available']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Book Information', {
            'fields': ('book', 'language', 'part_number', 'total_parts')
        }),
        ('Audio File', {
            'fields': ('audio_url', 'cloudinary_public_id')
        }),
        ('Metadata', {
            'fields': ('duration', 'file_size', 'is_available', 'chapter_timestamps')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def part_display(self, obj):
        if obj.total_parts > 1:
            return f"Part {obj.part_number}/{obj.total_parts}"
        return "Single Part"
    part_display.short_description = 'Part'
    
    def duration_formatted(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}:{seconds:02d}"
        return "-"
    duration_formatted.short_description = 'Duration'
    
    def file_size_kb(self, obj):
        if obj.file_size:
            return f"{obj.file_size // 1024} KB"
        return "-"
    file_size_kb.short_description = 'Size'


@admin.register(ChapterAudio)
class ChapterAudioAdmin(admin.ModelAdmin):
    list_display = ['book', 'chapter_number', 'language', 'duration_formatted', 'is_available', 'file_size_kb']
    list_filter = ['book', 'language', 'is_available']
    search_fields = ['book__name', 'language__name']
    list_editable = ['is_available']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Chapter Information', {
            'fields': ('book', 'chapter', 'chapter_number', 'language')
        }),
        ('Audio File', {
            'fields': ('audio_url', 'cloudinary_public_id')
        }),
        ('Metadata', {
            'fields': ('duration', 'file_size', 'is_available', 'start_time', 'end_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def duration_formatted(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes}:{seconds:02d}"
        return "-"
    duration_formatted.short_description = 'Duration'
    
    def file_size_kb(self, obj):
        if obj.file_size:
            return f"{obj.file_size // 1024} KB"
        return "-"
    file_size_kb.short_description = 'Size'


# ==================== QUIZ MODEL ADMINS ====================

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'book', 'chapter', 'level', 'correct_option', 'verse_reference']
    list_filter = ['book', 'level', 'correct_option']
    search_fields = ['book__name', 'verse_reference']
    
    fieldsets = (
        ('Question Information', {
            'fields': ('book', 'chapter', 'level', 'verse_reference')
        }),
        ('Answer', {
            'fields': ('correct_option',)
        }),
    )


@admin.register(QuestionText)
class QuestionTextAdmin(admin.ModelAdmin):
    list_display = ['question', 'language', 'text_preview']
    list_filter = ['language', 'question__book']
    search_fields = ['question__id', 'text']
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Text'


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ['question', 'label']
    list_filter = ['question__book']
    search_fields = ['question__id']


@admin.register(OptionText)
class OptionTextAdmin(admin.ModelAdmin):
    list_display = ['option', 'language', 'text_preview']
    list_filter = ['language', 'option__question__book']
    search_fields = ['text']
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Text'


@admin.register(Explanation)
class ExplanationAdmin(admin.ModelAdmin):
    list_display = ['question', 'language', 'text_preview']
    list_filter = ['language', 'question__book']
    search_fields = ['question__id', 'text']
    
    def text_preview(self, obj):
        return obj.text[:100] + '...' if len(obj.text) > 100 else obj.text
    text_preview.short_description = 'Text'


# ==================== USER PROGRESS ADMINS ====================

@admin.register(UserBookProgress)
class UserBookProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'current_chapter', 'current_verse', 'completed', 'progress_percentage', 'audio_progress']
    list_filter = ['book', 'completed']
    search_fields = ['user__username', 'book__name']
    readonly_fields = ['last_activity', 'last_audio_listened']
    
    def progress_percentage(self, obj):
        if obj.book.total_chapters > 0:
            percent = int((obj.current_chapter / obj.book.total_chapters) * 100)
            return format_html('<div style="background: #e9ecef; border-radius: 10px;"><div style="background: #28a745; width: {}%; border-radius: 10px; color: white; text-align: center;">{}%</div></div>', percent, percent)
        return "0%"
    progress_percentage.short_description = 'Reading Progress'
    
    def audio_progress(self, obj):
        completed = len(obj.audio_completed_chapters)
        if obj.book.total_chapters > 0:
            percent = int((completed / obj.book.total_chapters) * 100)
            return format_html('<span style="color: #007bff;">{}% ({}/{})</span>', percent, completed, obj.book.total_chapters)
        return "-"
    audio_progress.short_description = 'Audio Progress'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'book', 'level', 'score_percentage', 'status', 'started_at']
    list_filter = ['status', 'book', 'level']
    search_fields = ['user__username', 'book__name']
    readonly_fields = ['started_at', 'completed_at']


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_option', 'is_correct', 'answered_at']
    list_filter = ['is_correct']
    search_fields = ['attempt__user__username', 'question__id']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at', 'expires_at']
    list_filter = ['is_active']
    search_fields = ['user__username', 'token']
    readonly_fields = ['created_at', 'updated_at']


# ==================== CUSTOM ADMIN SITE SETTINGS ====================

admin.site.site_header = 'Bible Quiz Admin'
admin.site.site_title = 'Bible Quiz Admin Portal'
admin.site.index_title = 'Welcome to Bible Quiz Admin'