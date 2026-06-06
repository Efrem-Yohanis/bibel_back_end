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
            "psalms_part_1": "Psalms",
            "psalms_part_2": "Psalms",
            "psalms_part_3": "Psalms",
        }

        base_prefix = "bible_audio/bibel_audio/old/am/"
        all_resources = []
        next_cursor = None

        self.stdout.write("--- Downloading Complete Metadata Catalog from Cloudinary ---")

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

        with transaction.atomic():
            success_count = 0
            skipped_count = 0

            for asset in all_resources:
                public_id = asset.get("public_id")
                res_type = asset.get("resource_type", "video")

                path_parts = public_id.split('/')

                # ✅ FIX: Handle both path structures:
                #   6-part: bible_audio/bibel_audio/old/am/1_chronicles/1
                #   7-part: bible_audio/bibel_audio/old/am/genesis/scrambled_folder/1.mp3
                if len(path_parts) >= 6:
                    raw_book_folder = path_parts[4].strip().lower()
                    filename = path_parts[-1]

                    # Extract chapter number from filename (handles "1", "1.mp3", etc.)
                    clean_chapter_str = filename.split('.')[0]

                    if not clean_chapter_str.isdigit():
                        self.stdout.write(self.style.WARNING(f"⚠️ Skipping invalid file descriptor: {public_id}"))
                        skipped_count += 1
                        continue

                    true_chapter_num = int(clean_chapter_str)

                    # Determine book name from map or fallback to title-cased folder name
                    if raw_book_folder in book_name_map:
                        db_book_name = book_name_map[raw_book_folder]
                    else:
                        db_book_name = raw_book_folder.replace('_', ' ').title()

                    # Get or create the Book record
                    book, created_book = Book.objects.get_or_create(
                        name__iexact=db_book_name,
                        defaults={
                            'name': db_book_name,
                            'testament': testament,
                            'has_audio': True
                        }
                    )

                    if created_book:
                        self.stdout.write(f"📖 Created new book: {db_book_name}")

                    # Get or create the Chapter record
                    chapter, created_chapter = Chapter.objects.get_or_create(
                        book=book,
                        chapter_number=true_chapter_num,
                        defaults={'total_verses': 0}
                    )

                    # Build direct Cloudinary streaming URL
                    playback_url = f"https://res.cloudinary.com/dleykahqd/{res_type}/upload/{public_id}"

                    # Upsert the ChapterAudio record
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

                    if success_count % 100 == 0:
                        self.stdout.write(f"  ✅ Verified & Linked: {db_book_name} -> Chapter {true_chapter_num}")

                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ Unexpected path structure (< 6 parts): {public_id}"))
                    skipped_count += 1

            # Sync total_chapters and has_audio back to each Book
            self.stdout.write("\nRecalculating global book properties...")
            for book in Book.objects.filter(testament=testament):
                actual_chapter_count = Chapter.objects.filter(book=book).count()
                audio_count = ChapterAudio.objects.filter(book=book, language=language, is_available=True).count()
                if actual_chapter_count > 0:
                    book.total_chapters = actual_chapter_count
                if audio_count > 0:
                    book.has_audio = True
                book.save()

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ Perfect Linkage Complete!"
            f"\n   Processed : {success_count} audio maps"
            f"\n   Skipped   : {skipped_count} invalid entries"
        ))