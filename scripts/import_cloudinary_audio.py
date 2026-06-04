import os
import re
from django.core.management.base import BaseCommand
from django.db import transaction
import cloudinary
from cloudinary import api

# Import your database model layer
from core.models import Language, Testament, Book, Chapter, ChapterAudio

class Command(BaseCommand):
    help = "Validates and imports Cloudinary audio files mapping the true chapter filename to the correct Bible book."

    def handle(self, *args, **options):
        # 1. Initialize Cloudinary Configuration
        cloudinary.config(
            cloud_name="dleykahqd",
            api_key="284571752959753",
            api_secret="B-tJyF7f1oBSt9qIulbGNvK8Hbg",
            secure=True
        )

        # 2. Setup Core Database Relations
        language, _ = Language.objects.get_or_create(code="am", defaults={"name": "Amharic"})
        testament, _ = Testament.objects.get_or_create(name="Old")

        # Explicit map for tricky names to guarantee database matching
        book_name_map = {
            "1_chronicles": "1 Chronicles",
            "2_chronicles": "2 Chronicles",
            "1_kings": "1 Kings",
            "2_kings": "2 Kings",
            "1_samuel": "1 Samuel",
            "2_samuel": "2 Samuel",
            "song_of_solomon": "Song of Solomon",
            "psalms_part_1": "Psalms",  # Maps part 1 files directly to the main Psalms book
            "psalms_part_2": "Psalms",
            "psalms_part_3": "Psalms",
        }

        base_prefix = "bible_audio/bibel_audio/old/am/"
        all_resources = []
        next_cursor = None

        self.stdout.write(f"--- Downloading Complete Metadata Catalog from Cloudinary ---")
        
        # Paginate to fetch all files across the 500 safety barrier
        while True:
            kwargs = {
                "type": "upload",
                "resource_type": "video",
                "prefix": base_prefix,
                "max_results": 500
            }
            if next_cursor:
                kwargs["next_cursor"] = next_cursor
                
            response = api.resources(**kwargs)
            batch = response.get("resources", [])
            all_resources.extend(batch)
            
            self.stdout.write(f"Buffered {len(batch)} items... Total items tracking: {len(all_resources)}")
            
            next_cursor = response.get("next_cursor")
            if not next_cursor:
                break

        if not all_resources:
            self.stdout.write(self.style.WARNING("❌ No audio files detected in Cloudinary."))
            return

        self.stdout.write(f"\n--- Processing and Verifying Database Injection ---")

        # Atomic transaction means everything succeeds together, or nothing changes (prevents corruption)
        with transaction.atomic():
            success_count = 0
            
            for asset in all_resources:
                public_id = asset.get("public_id")
                res_type = asset.get("resource_type", "video")
                
                # Split pattern matches: bible_audio/bibel_audio/old/am/[book_folder]/[scrambled_folder]/[true_chapter_filename]
                path_parts = public_id.split('/')
                
                if len(path_parts) >= 7:
                    raw_book_folder = path_parts[4].strip().lower()
                    filename = path_parts[-1]
                    
                    # EXTRACT THE TRUE CHAPTER FROM FILENAME
                    # Extracts digits if the file has an extension like "1.mp3" or is just "1"
                    clean_chapter_str = filename.split('.')[0]
                    
                    if not clean_chapter_str.isdigit():
                        self.stdout.write(self.style.WARNING(f"⚠️ Skipping invalid file descriptor: {public_id}"))
                        continue
                        
                    true_chapter_num = int(clean_chapter_str)
                    
                    # DETERMINE CRITICAL BOOK NAME MATCHING
                    if raw_book_folder in book_name_map:
                        db_book_name = book_name_map[raw_book_folder]
                    else:
                        # Fallback parsing: turn "genesis" into "Genesis", "deuteronomy" into "Deuteronomy"
                        db_book_name = raw_book_folder.replace('_', ' ').title()
                    
                    # Query existing Book or generate a clean base record
                    book, created_book = Book.objects.get_or_create(
                        name__iexact=db_book_name,
                        defaults={
                            'name': db_book_name,
                            'testament': testament,
                            'has_audio': True
                        }
                    )
                    
                    # Ensure structural chapter constraint object exists
                    chapter, created_chapter = Chapter.objects.get_or_create(
                        book=book,
                        chapter_number=true_chapter_num,
                        defaults={'total_verses': 0}
                    )

                    # Build explicit, direct streaming URL
                    playback_url = f"https://res.cloudinary.com/dleykahqd/{res_type}/upload/{public_id}"

                    # Update or append the final audio url blueprint matching verified chapter targets
                    ChapterAudio.objects.update_or_create(
                        book=book,
                        chapter_number=true_chapter_num,
                        language=language,
                        defaults={
                            'chapter': chapter,
                            'audio_url': playback_url,
                            'cloudinary_public_id': public_id,
                            'is_available': True
                        }
                    )
                    
                    success_count += 1
                    
                    # Log mapping confirmations dynamically
                    if success_count % 100 == 0:
                        self.stdout.write(f" Verified & Linked: {db_book_name} -> Chapter {true_chapter_num}")

            # 4. Sync metadata counters back to the target Book instances
            self.stdout.write("\nRecalculating global book properties...")
            for book in Book.objects.filter(testament=testament):
                actual_chapter_count = Chapter.objects.filter(book=book).count()
                if actual_chapter_count > 0:
                    book.total_chapters = actual_chapter_count
                    book.has_audio = True
                    book.save()

        self.stdout.write(self.style.SUCCESS(f"\n✅ Perfect Linkage Complete! Processed {success_count} structural audio maps."))