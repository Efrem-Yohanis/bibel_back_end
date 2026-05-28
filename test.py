# insert_genesis_chapter26_audio.py
import os
import sys
from pathlib import Path

# Setup Django
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibel_project.settings')

import django
django.setup()

from core.models import Book, Language, ChapterAudio

def insert_chapter26_audio():
    """Insert Genesis Chapter 26 audio into database"""
    
    print("=" * 60)
    print("🔊 INSERTING GENESIS CHAPTER 26 AUDIO")
    print("=" * 60)
    
    # Get Genesis book
    try:
        book = Book.objects.get(name="Genesis")
        print(f"✅ Book: {book.name} (id={book.id})")
    except Book.DoesNotExist:
        print("❌ Book not found!")
        return
    
    # Get English language
    try:
        language = Language.objects.get(code='en')
        print(f"✅ Language: {language.name} (code={language.code})")
    except Language.DoesNotExist:
        print("❌ Language not found!")
        return
    
    # The Cloudinary URL from upload
    audio_url = "https://res.cloudinary.com/dleykahqd/video/upload/bible_audio/bibel_audio/old/en/genesis/26"
    
    # Or read from file
    # with open('genesis_chapter26_url.txt', 'r') as f:
    #     audio_url = f.read().strip()
    
    print(f"\n📝 Audio URL: {audio_url}")
    
    # Insert or update
    chapter_audio, created = ChapterAudio.objects.update_or_create(
        book=book,
        chapter_number=26,
        language=language,
        defaults={
            'audio_url': audio_url,
            'cloudinary_public_id': 'bible_audio/bibel_audio/old/en/genesis/26',
            'duration': None,  # You can update later if you have duration
            'file_size': None,  # You can update later
            'is_available': True
        }
    )
    
    if created:
        print("\n✅ Successfully created Chapter 26 audio!")
    else:
        print("\n🔄 Successfully updated Chapter 26 audio!")
    
    # Verify
    print("\n📊 Verification:")
    en_audio_count = ChapterAudio.objects.filter(
        book=book, 
        language=language, 
        is_available=True
    ).count()
    print(f"   English chapters with audio: {en_audio_count}/50")
    
    # Show Chapter 26 audio
    ch26 = ChapterAudio.objects.get(book=book, chapter_number=26, language=language)
    print(f"   Chapter 26 audio URL: {ch26.audio_url[:80]}...")
    
    print("\n" + "=" * 60)
    print("✅ Genesis Chapter 26 audio inserted successfully!")
    print("=" * 60)

def update_chapter26_duration():
    """Update duration if known (optional)"""
    
    # If you know the duration in seconds, you can update it
    # For example, if Chapter 26 is 145 seconds long:
    
    from core.models import ChapterAudio
    
    book = Book.objects.get(name="Genesis")
    language = Language.objects.get(code='en')
    
    chapter_audio = ChapterAudio.objects.get(
        book=book,
        chapter_number=26,
        language=language
    )
    
    # Update duration (replace 145 with actual duration)
    # chapter_audio.duration = 145
    # chapter_audio.save()
    # print("✅ Duration updated!")

if __name__ == "__main__":
    insert_chapter26_audio()
    # update_chapter26_duration()  # Uncomment to update duration