"""
nt_downloader.py — Downloads New Testament audio (books 40-66).
Saves flat:  old/Matthew/1.mp3  old/Mark/1.mp3  ...

Install:  pip install httpx
Run:      python nt_downloader.py
"""

import asyncio
import zipfile
import io
from pathlib import Path

import httpx

# ── Configuration ──────────────────────────────────────────────────────────────
DOWNLOAD_DIR   = Path.home() / "english_audio" / "old"
MAX_CONCURRENT = 5
TIMEOUT        = 120
RETRIES        = 3

NT_BOOKS = [
    "Matthew", "Mark", "Luke", "John", "Acts",
    "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy",
    "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John",
    "Jude", "Revelation",
]  # 27 books, numbers 40–66

# Try both known URL patterns — script will detect which one works
ZIP_PATTERNS = [
    "http://kjv.wordfree.net/bibles/app/audio/1_{num}.zip",   # same as OT
    "http://kjv.wordfree.net/bibles/app/audio/2_{num}.zip",   # possible NT prefix
]
# ───────────────────────────────────────────────────────────────────────────────


def already_done(book_name: str) -> bool:
    folder = DOWNLOAD_DIR / book_name
    return folder.exists() and any(folder.glob("*.mp3"))


def unzip_flat(data: bytes, book_name: str) -> int:
    """Extract mp3s directly into old/<BookName>/ with no subfolders."""
    dest = DOWNLOAD_DIR / book_name
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".mp3"):
                continue
            target = dest / Path(member).name
            target.write_bytes(zf.read(member))
            count += 1
    return count


async def download_book(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    book_num: int,
    book_name: str,
) -> tuple[int, bool, str]:

    if already_done(book_name):
        return book_num, True, f"skipped — {book_name} already exists"

    async with semaphore:
        for attempt in range(1, RETRIES + 1):
            # Try each URL pattern until one works
            last_msg = ""
            for pattern in ZIP_PATTERNS:
                url = pattern.format(num=book_num)
                try:
                    resp = await client.get(url, timeout=TIMEOUT)
                    resp.raise_for_status()
                    count = unzip_flat(resp.content, book_name)
                    return book_num, True, f"{book_name}: {count} files  [{url}]"
                except httpx.HTTPStatusError as e:
                    last_msg = f"HTTP {e.response.status_code} on {url}"
                except httpx.TimeoutException:
                    last_msg = f"timeout on {url}"
                except Exception as e:
                    last_msg = str(e)

            if attempt < RETRIES:
                await asyncio.sleep(2 ** attempt)

    return book_num, False, f"{book_name}: failed — {last_msg}"


async def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BibleDownloader/2.0)"},
    ) as client:
        tasks = [
            download_book(client, semaphore, num, name)
            for num, name in zip(range(40, 67), NT_BOOKS)
        ]
        print(f"Downloading {len(tasks)} NT books ({MAX_CONCURRENT} concurrent)\n")
        results = await asyncio.gather(*tasks)

    ok = skipped = failed = 0
    for book_num, success, msg in sorted(results):
        icon = "✓" if success else "✗"
        print(f"  [{icon}] {book_num}. {msg}")
        if not success:
            failed += 1
        elif "skipped" in msg:
            skipped += 1
        else:
            ok += 1

    print(f"\nDone — downloaded: {ok}  skipped: {skipped}  failed: {failed}")
    print(f"Files in: {DOWNLOAD_DIR}")


if __name__ == "__main__":
    asyncio.run(main())