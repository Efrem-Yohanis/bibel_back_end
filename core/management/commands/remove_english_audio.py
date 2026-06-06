"""
Django management command: remove_english_audio

Place this file at:
    core/management/commands/remove_english_audio.py

Usage
-----
python manage.py remove_english_audio --dry-run
python manage.py remove_english_audio
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import ChapterAudio, Language


class Command(BaseCommand):
    help = "Remove all English audio records from ChapterAudio table (both Old & New Testament)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Show what would be deleted without actually deleting.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN — nothing will be deleted.\n"))

        # Get the English language
        try:
            english = Language.objects.get(code="en")
        except Language.DoesNotExist:
            self.stdout.write(self.style.ERROR("English language not found in DB."))
            return

        # Find all English audio records
        english_audios = ChapterAudio.objects.filter(language=english).select_related("book")

        count = english_audios.count()
        self.stdout.write(f"Found {count} English audio record(s).\n")

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No English audio to delete."))
            return

        # Show what will be deleted
        for audio in english_audios.order_by("book__name", "chapter_number")[:20]:
            self.stdout.write(f"  • {audio.book.name} ch.{audio.chapter_number}")

        if count > 20:
            self.stdout.write(f"  ... and {count - 20} more")

        self.stdout.write("")

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY-RUN] Would delete {count} record(s)."))
            return

        # Confirm deletion
        self.stdout.write(self.style.WARNING(f"About to delete {count} English audio record(s)..."))
        confirm = input("Type 'yes' to confirm deletion: ")
        
        if confirm.lower() != "yes":
            self.stdout.write(self.style.ERROR("Deletion cancelled."))
            return

        # Delete
        with transaction.atomic():
            deleted_count, _ = english_audios.delete()

        self.stdout.write(self.style.SUCCESS(f"\n✓ Deleted {deleted_count} English audio record(s)."))
