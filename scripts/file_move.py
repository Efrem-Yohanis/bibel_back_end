import shutil
from pathlib import Path

DOWNLOAD_DIR = Path.home() / "english_audio" / "old"

BOOK_NAMES = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi",
]

for i, name in enumerate(BOOK_NAMES, start=1):
    old_folder = DOWNLOAD_DIR / f"book_{i:02d}"
    new_folder = DOWNLOAD_DIR / name

    if not old_folder.exists():
        print(f"  [!] book_{i:02d} not found, skipping")
        continue

    new_folder.mkdir(exist_ok=True)

    # Move all mp3s from any subfolder directly into the named folder
    for mp3 in old_folder.rglob("*.mp3"):
        shutil.move(str(mp3), str(new_folder / mp3.name))

    # Delete the old folder
    shutil.rmtree(old_folder)
    print(f"  [✓] book_{i:02d}  →  {name}")

print("\nDone.")