"""
split_and_upload.py

Step 1 — Moves OT books into  english_audio/ot/
          Moves NT books into  english_audio/nt/

Step 2 — Uploads both to Cloudinary via direct HTTP (no SDK conflicts)
          old/ → bible_audio/bibel_audio/old/en/<book>/<chapter>
          new/ → bible_audio/bibel_audio/new/en/<book>/<chapter>

Step 3 — Saves JSON url maps to english_audio/url_maps/

Install:  pip install httpx
Run:      python split_and_upload.py
"""

import base64
import hashlib
import hmac
import json
import shutil
import time
from pathlib import Path

import httpx

# ── Cloudinary credentials ────────────────────────────────────────────────────
CLOUD_NAME = "dleykahqd"
API_KEY    = "284571752959753"
API_SECRET = "B-tJyF7f1oBSt9qIulbGNvK8Hbg"
UPLOAD_URL = f"https://api.cloudinary.com/v1_1/{CLOUD_NAME}/video/upload"

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE     = Path.home() / "english_audio"
SOURCE   = BASE / "old"
OT_DIR   = BASE / "ot"
NT_DIR   = BASE / "nt"
JSON_OUT = BASE / "url_maps"
JSON_OUT.mkdir(parents=True, exist_ok=True)

# ── Book lists ────────────────────────────────────────────────────────────────
OT_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra",
    "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations",
    "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
    "Zephaniah", "Haggai", "Zechariah", "Malachi",
]

NT_BOOKS = [
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy",
    "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation",
]


# ─────────────────────────────────────────────────────────────────────────────
# Cloudinary signed upload (no SDK — pure HTTP)
# ─────────────────────────────────────────────────────────────────────────────
def sign(params: dict) -> str:
    """Generate Cloudinary upload signature."""
    # Sort params alphabetically, join as key=value&...
    to_sign = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    to_sign += API_SECRET
    return hashlib.sha256(to_sign.encode()).hexdigest()


def upload_file(client: httpx.Client, mp3: Path, public_id: str) -> str | None:
    """Upload one mp3 to Cloudinary. Returns secure_url or None on failure."""
    timestamp = str(int(time.time()))
    params = {
        "public_id": public_id,
        "overwrite": "false",
        "timestamp": timestamp,
    }
    signature = sign(params)

    with open(mp3, "rb") as f:
        files = {"file": (mp3.name, f, "audio/mpeg")}
        data  = {**params, "api_key": API_KEY, "signature": signature}

        try:
            resp = client.post(UPLOAD_URL, data=data, files=files, timeout=120)
            if resp.status_code == 200:
                return resp.json()["secure_url"]
            # 400 with "already exists" is fine — build the URL manually
            body = resp.json()
            if "already exists" in str(body.get("error", {}).get("message", "")):
                return f"https://res.cloudinary.com/{CLOUD_NAME}/video/upload/{public_id}"
            print(f"      API error: {body.get('error', {}).get('message', resp.text)}")
            return None
        except Exception as e:
            print(f"      Exception: {e}")
            return None


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Split
# ─────────────────────────────────────────────────────────────────────────────
def split():
    OT_DIR.mkdir(parents=True, exist_ok=True)
    NT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("STEP 1 — Splitting into ot/ and nt/")
    print("=" * 60)

    for name in OT_BOOKS:
        src, dst = SOURCE / name, OT_DIR / name
        if src.exists() and not dst.exists():
            shutil.move(str(src), str(dst))
            print(f"  [OT] {name}")
        elif dst.exists():
            print(f"  [OT] {name} — already in ot/")

    for name in NT_BOOKS:
        src, dst = SOURCE / name, NT_DIR / name
        if src.exists() and not dst.exists():
            shutil.move(str(src), str(dst))
            print(f"  [NT] {name}")
        elif dst.exists():
            print(f"  [NT] {name} — already in nt/")

    print("\nSplit complete.\n")


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Upload
# ─────────────────────────────────────────────────────────────────────────────
ALL_URLS: dict = {}


def upload_testament(local_dir: Path, cloudinary_prefix: str, label: str):
    book_folders = sorted(d for d in local_dir.iterdir() if d.is_dir())
    print(f"\n{'='*60}")
    print(f"  {label}  ({len(book_folders)} books)  →  {cloudinary_prefix}")
    print(f"{'='*60}")

    with httpx.Client() as client:
        for book_folder in book_folders:
            book_name = book_folder.name
            book_key  = book_name.lower().replace(" ", "_")
            urls: dict[str, str] = {}

            mp3_files = sorted(book_folder.glob("*.mp3"), key=lambda p: int(p.stem))
            if not mp3_files:
                print(f"  [!] No mp3s in {book_name}, skipping")
                continue

            print(f"\n  📖 {book_name} ({len(mp3_files)} chapters)")

            for mp3 in mp3_files:
                chapter   = mp3.stem
                public_id = f"{cloudinary_prefix}/{book_key}/{chapter}"
                url = upload_file(client, mp3, public_id)

                if url:
                    urls[chapter] = url
                    print(f"    ✓ Ch {chapter:>3}  {url}")
                else:
                    print(f"    ✗ Ch {chapter} failed — will retry on next run")
                    time.sleep(1)

            if urls:
                ALL_URLS[book_name] = urls
                out = JSON_OUT / f"{book_name}.json"
                out.write_text(json.dumps(urls, indent=4), encoding="utf-8")
                print(f"  💾 Saved {out.name}")


def upload():
    upload_testament(OT_DIR, "bible_audio/bibel_audio/old/en", "Old Testament")
    upload_testament(NT_DIR, "bible_audio/bibel_audio/new/en", "New Testament")

    combined = JSON_OUT / "_all_books.json"
    combined.write_text(json.dumps(ALL_URLS, indent=4), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"✅ Done!  Books: {len(ALL_URLS)}   JSON: {combined}")
    print(f"{'='*60}")


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    split()
    upload()