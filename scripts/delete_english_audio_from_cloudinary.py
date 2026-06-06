"""
Script: delete_english_audio_from_cloudinary.py

Remove all English audio files from Cloudinary (both New & Old Testament).

Usage
-----
python scripts/delete_english_audio_from_cloudinary.py --dry-run
python scripts/delete_english_audio_from_cloudinary.py
"""

import os
import sys
import cloudinary
from cloudinary import api


# Cloudinary config
CLOUDINARY_CONFIG = {
    "cloud_name": os.environ.get("CLOUDINARY_NAME", "dleykahqd"),
    "api_key":    os.environ.get("CLOUDINARY_API_KEY", "284571752959753"),
    "api_secret": os.environ.get("CLOUDINARY_API_SECRET", "B-tJyF7f1oBSt9qIulbGNvK8Hbg"),
    "secure":     True,
}


def fetch_all_resources(prefix: str) -> list:
    """Paginate through Cloudinary API and fetch all assets under prefix."""
    all_resources = []
    next_cursor = None
    
    print(f"  Fetching resources from: {prefix}")
    
    while True:
        kwargs = {
            "type":          "upload",
            "resource_type": "video",
            "prefix":        prefix,
            "max_results":   500,
        }
        if next_cursor:
            kwargs["next_cursor"] = next_cursor
        
        response = api.resources(**kwargs)
        batch = response.get("resources", [])
        all_resources.extend(batch)
        
        print(f"    Fetched {len(batch)} assets (total so far: {len(all_resources)})")
        
        next_cursor = response.get("next_cursor")
        if not next_cursor:
            break
    
    return all_resources


def delete_resources(public_ids: list, dry_run=False) -> int:
    """Delete resources from Cloudinary. Returns count of deleted items."""
    if not public_ids:
        return 0
    
    if dry_run:
        print(f"  [DRY-RUN] Would delete {len(public_ids)} file(s)")
        return len(public_ids)
    
    # Delete in batches of 100 (Cloudinary API limit)
    deleted_count = 0
    for i in range(0, len(public_ids), 100):
        batch = public_ids[i:i+100]
        try:
            result = api.delete_resources(batch)
            # Cloudinary returns: {"deleted": {public_id: "deleted", ...}}
            deleted_items = result.get("deleted", {})
            deleted_count += len(deleted_items)
            print(f"  Deleted batch {i//100 + 1}: {len(deleted_items)} file(s)")
        except Exception as e:
            print(f"  ✖ Error deleting batch: {e}")
    
    return deleted_count


def main():
    """Delete all English audio files from Cloudinary."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Delete English audio from Cloudinary")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()
    
    dry_run = args.dry_run
    
    cloudinary.config(**CLOUDINARY_CONFIG)
    
    if dry_run:
        print("DRY-RUN — nothing will be deleted.\n")
    
    print("Scanning Cloudinary for English audio files...\n")
    
    all_public_ids = []
    
    # Fetch NEW Testament English audio
    print("NEW Testament (bible_audio/bibel_audio/new/en/):")
    new_resources = fetch_all_resources("bible_audio/bibel_audio/new/en/")
    new_public_ids = [r["public_id"] for r in new_resources]
    all_public_ids.extend(new_public_ids)
    print(f"  → Found {len(new_resources)} file(s)\n")
    
    # Fetch OLD Testament English audio
    print("OLD Testament (bible_audio/bibel_audio/old/en/):")
    old_resources = fetch_all_resources("bible_audio/bibel_audio/old/en/")
    old_public_ids = [r["public_id"] for r in old_resources]
    all_public_ids.extend(old_public_ids)
    print(f"  → Found {len(old_resources)} file(s)\n")
    
    total = len(all_public_ids)
    
    if total == 0:
        print("No English audio files found in Cloudinary.")
        return
    
    print(f"Total English audio files: {total}\n")
    
    # Show sample
    print("Sample files to be deleted:")
    for pid in all_public_ids[:10]:
        print(f"  • {pid}")
    if total > 10:
        print(f"  ... and {total - 10} more\n")
    
    if dry_run:
        print(f"[DRY-RUN] Would delete {total} file(s) from Cloudinary.")
        return
    
    # Confirm deletion
    print(f"⚠️  About to permanently delete {total} file(s) from Cloudinary...")
    confirm = input("Type 'yes' to confirm deletion: ")
    
    if confirm.lower() != "yes":
        print("Deletion cancelled.")
        return
    
    print("\nDeleting files from Cloudinary...\n")
    
    deleted = delete_resources(all_public_ids, dry_run=False)
    
    print(f"\n✓ Deleted {deleted} English audio file(s) from Cloudinary.")


if __name__ == "__main__":
    main()
