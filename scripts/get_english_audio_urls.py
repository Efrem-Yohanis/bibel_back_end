"""
Script: get_english_audio_urls.py

Fetch all English audio URLs from Cloudinary (both New & Old Testament).
Outputs results as JSON for easy inspection or further processing.

Usage
-----
python scripts/get_english_audio_urls.py
python scripts/get_english_audio_urls.py > english_audio_urls.json
"""

import os
import re
import json
import cloudinary
from cloudinary import api


# Cloudinary config
CLOUDINARY_CONFIG = {
    "cloud_name": os.environ.get("CLOUDINARY_NAME", "dleykahqd"),
    "api_key":    os.environ.get("CLOUDINARY_API_KEY", "284571752959753"),
    "api_secret": os.environ.get("CLOUDINARY_API_SECRET", "B-tJyF7f1oBSt9qIulbGNvK8Hbg"),
    "secure":     True,
}

# Map Cloudinary folder names to book display names
BOOK_NAME_MAP = {
    "genesis":          "Genesis",
    "exodus":           "Exodus",
    "leviticus":        "Leviticus",
    "numbers":          "Numbers",
    "deuteronomy":      "Deuteronomy",
    "joshua":           "Joshua",
    "judges":           "Judges",
    "ruth":             "Ruth",
    "1_samuel":         "1 Samuel",
    "2_samuel":         "2 Samuel",
    "1_kings":          "1 Kings",
    "2_kings":          "2 Kings",
    "1_chronicles":     "1 Chronicles",
    "2_chronicles":     "2 Chronicles",
    "ezra":             "Ezra",
    "nehemiah":         "Nehemiah",
    "esther":           "Esther",
    "job":              "Job",
    "psalms":           "Psalms",
    "psalm":            "Psalms",
    "psalms_part_1":    "Psalms (Part 1)",
    "psalms_part_2":    "Psalms (Part 2)",
    "psalms_part_3":    "Psalms (Part 3)",
    "proverbs":         "Proverbs",
    "ecclesiastes":     "Ecclesiastes",
    "song_of_solomon":  "Song of Solomon",
    "song_of_songs":    "Song of Solomon",
    "isaiah":           "Isaiah",
    "jeremiah":         "Jeremiah",
    "lamentations":     "Lamentations",
    "ezekiel":          "Ezekiel",
    "daniel":           "Daniel",
    "hosea":            "Hosea",
    "joel":             "Joel",
    "amos":             "Amos",
    "obadiah":          "Obadiah",
    "jonah":            "Jonah",
    "micah":            "Micah",
    "nahum":            "Nahum",
    "habakkuk":         "Habakkuk",
    "zephaniah":        "Zephaniah",
    "haggai":           "Haggai",
    "zechariah":        "Zechariah",
    "malachi":          "Malachi",
    "matthew":          "Matthew",
    "mark":             "Mark",
    "luke":             "Luke",
    "john":             "John",
    "acts":             "Acts",
    "acts_part1":       "Acts",
    "acts_part2":       "Acts",
    "romans":           "Romans",
    "1_corinthians":    "1 Corinthians",
    "2_corinthians":    "2 Corinthians",
    "galatians":        "Galatians",
    "ephesians":        "Ephesians",
    "philippians":      "Philippians",
    "colossians":       "Colossians",
    "1_thessalonians":  "1 Thessalonians",
    "2_thessalonians":  "2 Thessalonians",
    "1_timothy":        "1 Timothy",
    "2_timothy":        "2 Timothy",
    "titus":            "Titus",
    "philemon":         "Philemon",
    "hebrews":          "Hebrews",
    "james":            "James",
    "1_peter":          "1 Peter",
    "2_peter":          "2 Peter",
    "1_john":           "1 John",
    "2_john":           "2 John",
    "3_john":           "3 John",
    "jude":             "Jude",
    "revelation":       "Revelation",
    "john_part1":       "John",
    "john_part2":       "John",
    "luke_part1":       "Luke",
    "luke_part2":       "Luke",
    "mark_part1":       "Mark",
    "mark_part2":       "Mark",
    "matthew_part1":    "Matthew",
    "matthew_part2":    "Matthew",
}


def normalize_folder_name(folder_name: str) -> str:
    """Normalize Cloudinary folder name for mapping lookup."""
    folder = folder_name.strip().lower()
    folder = folder.replace(" ", "_")
    folder = folder.replace("-", "_")
    folder = re.sub(r"__+", "_", folder)
    folder = folder.strip("_")
    return folder


def get_book_display_name(folder_name: str) -> str:
    """Get English book display name from Cloudinary folder name."""
    normalized = normalize_folder_name(folder_name)
    if normalized in BOOK_NAME_MAP:
        return BOOK_NAME_MAP[normalized]
    # Fallback: convert underscores to title case
    return folder_name.replace("_", " ").title()


def fetch_all_resources(prefix: str) -> list:
    """Paginate through Cloudinary API and fetch all assets under prefix."""
    all_resources = []
    next_cursor = None
    
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
        
        print(f"  Fetched {len(batch)} assets from {prefix}")
        
        next_cursor = response.get("next_cursor")
        if not next_cursor:
            break
    
    return all_resources


def extract_audio_data(resources: list) -> list:
    """Extract book, chapter, and URL from Cloudinary resources."""
    audio_data = []
    
    for asset in resources:
        public_id = asset.get("public_id", "")
        res_type = asset.get("resource_type", "video")
        parts = public_id.split("/")
        
        # Expected format: bible_audio/bibel_audio/{testament}/{lang}/{book_folder}/{file}
        if len(parts) < 6:
            continue
        
        testament = parts[2]  # 'new' or 'old'
        lang = parts[3]       # 'en', 'am', etc.
        book_folder = parts[4]
        filename = parts[-1]
        
        # Extract chapter number from filename (e.g., "1.mp3" -> 1)
        chapter_match = re.match(r"^(\d+)", filename)
        if not chapter_match:
            continue
        
        chapter_num = int(chapter_match.group(1))
        book_name = get_book_display_name(book_folder)
        
        # Build playback URL
        cloud_name = CLOUDINARY_CONFIG["cloud_name"]
        playback_url = f"https://res.cloudinary.com/{cloud_name}/{res_type}/upload/{public_id}"
        
        audio_data.append({
            "testament": testament.upper(),
            "book": book_name,
            "chapter": chapter_num,
            "cloudinary_folder": book_folder,
            "filename": filename,
            "public_id": public_id,
            "playback_url": playback_url,
        })
    
    return audio_data


def main():
    """Fetch and output all English audio URLs from Cloudinary."""
    cloudinary.config(**CLOUDINARY_CONFIG)
    
    print("Fetching English audio URLs from Cloudinary...\n")
    
    all_audio = []
    
    # Fetch NEW Testament
    print("Scanning: bible_audio/bibel_audio/new/en/")
    new_resources = fetch_all_resources("bible_audio/bibel_audio/new/en/")
    new_audio = extract_audio_data(new_resources)
    all_audio.extend(new_audio)
    print(f"  → Found {len(new_audio)} audio files\n")
    
    # Fetch OLD Testament
    print("Scanning: bible_audio/bibel_audio/old/en/")
    old_resources = fetch_all_resources("bible_audio/bibel_audio/old/en/")
    old_audio = extract_audio_data(old_resources)
    all_audio.extend(old_audio)
    print(f"  → Found {len(old_audio)} audio files\n")
    
    # Sort by testament, then book, then chapter
    all_audio.sort(key=lambda x: (x["testament"], x["book"], x["chapter"]))
    
    # Output as JSON
    output = {
        "total_files": len(all_audio),
        "new_testament_count": len(new_audio),
        "old_testament_count": len(old_audio),
        "audio_files": all_audio,
    }
    
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
