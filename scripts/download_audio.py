"""
Bible Audio Downloader — Fast async parallel version
No browser, no ChromeDriver. Uses httpx + asyncio.

Install deps:
    pip install httpx

Run:
    python bible_downloader.py
"""

import asyncio
import zipfile
import io
from pathlib import Path

import httpx

# ── Configuration ──────────────────────────────────────────────────────────────
DOWNLOAD_DIR   = Path.home() / "english_audio" / "old"
START_BOOK     = 1
END_BOOK       = 39
MAX_CONCURRENT = 5          # parallel downloads at once (raise to 8-10 if your connection is fast)
TIMEOUT        = 120        # seconds per download before giving up
RETRIES        = 3          # retry attempts on failure

# URL template — zero-padded book number e.g. 1_01.zip, 1_02.zip …
# Adjust this pattern if the site uses different naming
ZIP_URL = "http://kjv.wordfree.net/bibles/app/audio/1_{:d}.zip"
# ───────────────────────────────────────────────────────────────────────────────


def already_done(book_num: int) -> bool:
    """Skip books whose output folder already exists (idempotent re-runs)."""
    return (DOWNLOAD_DIR / f"book_{book_num:02d}").exists()


def unzip_in_memory(data: bytes, book_num: int) -> int:
    """Extract ZIP bytes directly into the output folder. Returns file count."""
    extract_to = DOWNLOAD_DIR / f"book_{book_num:02d}"
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(extract_to)
        return len(zf.namelist())


async def download_book(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    book_num: int,
) -> tuple[int, bool, str]:
    """Download, extract, and return (book_num, success, message)."""

    if already_done(book_num):
        return book_num, True, "skipped (already exists)"

    url = ZIP_URL.format(book_num)

    async with semaphore:                        # limit concurrency
        for attempt in range(1, RETRIES + 1):
            try:
                resp = await client.get(url, timeout=TIMEOUT)
                resp.raise_for_status()

                count = unzip_in_memory(resp.content, book_num)
                return book_num, True, f"extracted {count} files"

            except httpx.HTTPStatusError as e:
                msg = f"HTTP {e.response.status_code}"
            except httpx.TimeoutException:
                msg = "timeout"
            except Exception as e:
                msg = str(e)

            if attempt < RETRIES:
                await asyncio.sleep(2 ** attempt)   # exponential back-off
            else:
                return book_num, False, f"failed after {RETRIES} attempts — {msg}"


async def main():
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    # Shared async HTTP client — connection pooling, keep-alive, HTTP/2
    async with httpx.AsyncClient(
        follow_redirects=True,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BibleDownloader/2.0)"},
        http2=True,           # faster if the server supports it (falls back gracefully)
    ) as client:

        tasks = [
            download_book(client, semaphore, n)
            for n in range(START_BOOK, END_BOOK + 1)
        ]

        print(f"Starting download of books {START_BOOK}–{END_BOOK} "
              f"({MAX_CONCURRENT} concurrent)\n")

        results = await asyncio.gather(*tasks)

    # ── Summary ────────────────────────────────────────────────────────────────
    ok = skipped = failed = 0
    for book_num, success, msg in sorted(results):
        status = "✓" if success else "✗"
        print(f"  [{status}] Book {book_num:02d}: {msg}")
        if not success:
            failed += 1
        elif "skipped" in msg:
            skipped += 1
        else:
            ok += 1

    print(f"\nDone — downloaded: {ok}  skipped: {skipped}  failed: {failed}")
    print(f"Files saved to: {DOWNLOAD_DIR}")


if __name__ == "__main__":
    asyncio.run(main())