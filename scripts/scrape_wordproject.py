import json
import os
import re
import time
import concurrent.futures
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ── Only Joshua from OT ───────────────────────────────────────────────────────
# Joshua is OT book #6
OT_BOOKS_TO_SCRAPE = [
    (6, "joshua"),
]

# ── All 27 NT books ───────────────────────────────────────────────────────────
# wordproject.org numbers NT books 40–66
NEW_TESTAMENT_BOOKS = [
    (40, "matthew"),      (41, "mark"),          (42, "luke"),
    (43, "john"),         (44, "acts"),           (45, "romans"),
    (46, "1_corinthians"),(47, "2_corinthians"),  (48, "galatians"),
    (49, "ephesians"),    (50, "philippians"),    (51, "colossians"),
    (52, "1_thessalonians"),(53,"2_thessalonians"),(54,"1_timothy"),
    (55, "2_timothy"),    (56, "titus"),          (57, "philemon"),
    (58, "hebrews"),      (59, "james"),          (60, "1_peter"),
    (61, "2_peter"),      (62, "1_john"),         (63, "2_john"),
    (64, "3_john"),       (65, "jude"),           (66, "revelation"),
]

# ── Speed settings ────────────────────────────────────────────────────────────
MAX_CHAPTER_WORKERS = 6   # parallel chapter fetches per book
INTER_CHAPTER_DELAY = 0.05  # seconds between chapter requests (per thread)
INTER_BOOK_DELAY    = 0.3   # seconds between books


def make_session():
    """Reusable session with retries and connection pooling."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3,
                  status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    return session


SESSION = make_session()


def scrape_bible_chapter(url):
    try:
        response = SESSION.get(url, timeout=10)
        response.encoding = "utf-8"

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        text_body = soup.find("div", id="textBody")
        if not text_body:
            return None

        chapter_title_element = text_body.find("h3")
        chapter_title = (
            chapter_title_element.text.strip()
            if chapter_title_element
            else "Unknown Chapter"
        )

        p_tag = text_body.find("p")
        if not p_tag:
            return None

        p_html = str(p_tag)
        p_html_cleaned = re.sub(
            r'<[^>]*class="[^"]*comment[^"]*"[^>]*>.*?</[^>]+>',
            "", p_html, flags=re.DOTALL
        )
        clean_p_soup = BeautifulSoup(p_html_cleaned, "html.parser")

        for br in clean_p_soup.find_all("br"):
            br.replace_with("\n")
        for span in clean_p_soup.find_all("span"):
            span.insert_before("\n")

        lines = clean_p_soup.get_text().split("\n")
        verses_list = []
        current_verse_num = 1

        for line in lines:
            cleaned_line = line.strip().lstrip("፤ ").strip()
            if not cleaned_line:
                continue
            match = re.match(r"^(\d+)\s*፤?\s*(.*)$", cleaned_line)
            if match:
                current_verse_num = int(match.group(1))
                verse_text = match.group(2).strip().lstrip("፤ ").strip()
            else:
                verse_text = cleaned_line
            if verse_text:
                verses_list.append({"verse": current_verse_num, "text": verse_text})

        return {"chapter_title": chapter_title, "verses": verses_list}

    except Exception as e:
        print(f"\n  [error] {url}: {e}")
        return None


def fetch_chapter_task(args):
    """Worker target: fetch one chapter and return (chapter_num, result)."""
    book_number, chapter_num = args
    url = f"https://www.wordproject.org/bibles/am/{book_number:02d}/{chapter_num}.htm"
    time.sleep(INTER_CHAPTER_DELAY)
    return chapter_num, scrape_bible_chapter(url)


def probe_chapter_count(book_number):
    """
    Fast binary-search to find the last valid chapter number,
    avoiding the slow one-by-one 404 crawl.
    Falls back to sequential scan if binary search is unreliable.
    """
    # First, confirm chapter 1 exists
    _, result = fetch_chapter_task((book_number, 1))
    if result is None:
        return 0

    # Binary search upper bound: double until we hit a 404
    lo, hi = 1, 1
    while True:
        _, r = fetch_chapter_task((book_number, hi * 2))
        if r is None:
            break
        hi *= 2
        if hi > 200:   # safety cap
            break

    # Binary search in [lo, hi]
    while lo < hi:
        mid = (lo + hi + 1) // 2
        _, r = fetch_chapter_task((book_number, mid))
        if r is None:
            hi = mid - 1
        else:
            lo = mid

    return lo


def scrape_full_book(book_number, book_name_en, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    print(f"  Probing chapter count for {book_name_en}...", end=" ", flush=True)
    total_chapters = probe_chapter_count(book_number)
    if total_chapters == 0:
        print(f"0 — skipping.")
        return False
    print(f"{total_chapters} chapters found.")

    # Fetch all chapters in parallel
    tasks = [(book_number, ch) for ch in range(1, total_chapters + 1)]
    results = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CHAPTER_WORKERS) as executor:
        futures = {executor.submit(fetch_chapter_task, t): t for t in tasks}
        done_count = 0
        for future in concurrent.futures.as_completed(futures):
            chapter_num, chapter_result = future.result()
            done_count += 1
            print(f"  -> {done_count}/{total_chapters} chapters fetched", end="\r", flush=True)
            if chapter_result is not None:
                results[chapter_num] = chapter_result

    # Assemble in order
    chapters = []
    for ch in range(1, total_chapters + 1):
        if ch in results:
            chapters.append({
                "chapter": ch,
                "title": results[ch]["chapter_title"],
                "verses": results[ch]["verses"],
            })

    if not chapters:
        print(f"\n  No chapters saved for {book_name_en}.")
        return False

    book_data = {"book": book_name_en, "chapters": chapters}
    filename = os.path.join(output_dir, f"{book_name_en}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(book_data, f, ensure_ascii=False, indent=2)
    print(f"\n  ✓ Saved {book_name_en}.json ({len(chapters)} chapters)")
    return True


if __name__ == "__main__":
    start_total = time.time()

    # ── Joshua (OT) ───────────────────────────────────────────────────────────
    ot_folder = "am_book"
    print(f"\n=== OLD TESTAMENT (Joshua only) → '{ot_folder}/' ===\n")
    for book_number, book_name in OT_BOOKS_TO_SCRAPE:
        print(f"[OT] {book_name.upper()} (URL code: {book_number:02d})")
        scrape_full_book(book_number=book_number, book_name_en=book_name, output_dir=ot_folder)
        time.sleep(INTER_BOOK_DELAY)

    # ── New Testament ─────────────────────────────────────────────────────────
    nt_folder = "newtesmane_am"
    print(f"\n=== NEW TESTAMENT (all 27 books) → '{nt_folder}/' ===\n")
    for book_number, book_name in NEW_TESTAMENT_BOOKS:
        print(f"[NT {book_number}] {book_name.upper()}")
        scrape_full_book(book_number=book_number, book_name_en=book_name, output_dir=nt_folder)
        time.sleep(INTER_BOOK_DELAY)

    elapsed = time.time() - start_total
    mins, secs = divmod(int(elapsed), 60)
    print(f"\n✓ All done in {mins}m {secs}s")
    print(f"  OT Joshua  → {ot_folder}/joshua.json")
    print(f"  NT 27 books → {nt_folder}/")