from django.contrib import admin
from .models import *

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'native_name', 'is_active']
    search_fields = ['code', 'name']

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['level_number', 'name', 'icon', 'color']

@admin.register(Testament)
class TestamentAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['name', 'testament']
    list_filter = ['testament']
    search_fields = ['name']

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['book', 'chapter_number']
    list_filter = ['book']

@admin.register(Verse)
class VerseAdmin(admin.ModelAdmin):
    list_display = ['chapter', 'verse_number']

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_active', 'is_admin', 'created_at']
    list_filter = ['is_active', 'is_admin']
    search_fields = ['username', 'email']