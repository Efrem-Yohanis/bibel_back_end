import json
import os
import re
import time
from bs4 import BeautifulSoup
import requests

# List of English names for the 39 Old Testament books in order
# This ensures files are named cleanly (e.g., genesis.json, exodus.json)
OLD_TESTAMENT_BOOKS = [
    "genesis", "exodus", "leviticus", "numbers", "deuteronomy",
    "joshua", "judges", "ruth", "1_samuel", "2_samuel",
    "1_kings", "2_kings", "1_chronicles", "2_chronicles", "ezra",
    "nehemiah", "esther", "job", "psalms", "proverbs",
    "ecclesiastes", "song_of_solomon", "isaiah", "jeremiah", "lamentations",
    "ezekiel", "daniel", "hosea", "joel", "amos",
    "obadiah", "jonah", "micah", "nahum", "habakkuk",
    "zephaniah", "haggai", "zechariah", "malachi"
]

def scrape_bible_chapter(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
        # Fixed the missing regex string to clear comments correctly
        p_html_cleaned = re.sub(r"", "", p_html, flags=re.DOTALL)
        clean_p_soup = BeautifulSoup(p_html_cleaned, "html.parser")

        verses_list = []

        for br in clean_p_soup.find_all("br"):
            br.replace_with("\n")
        for span in clean_p_soup.find_all("span"):
            span.insert_before("\n")

        lines = clean_p_soup.get_text().split("\n")

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
        print(f"\nError requesting {url}: {e}")
        return None


def scrape_full_book(book_number, book_name_en, output_dir="am_book"):
    book_data = {"book": book_name_en, "chapters": []}
    chapter_num = 1
    
    # Ensure the target directory exists
    os.makedirs(output_dir, exist_ok=True)

    while True:
        formatted_book = f"{book_number:02d}"
        url = f"https://www.wordproject.org/bibles/am/{formatted_book}/{chapter_num}.htm"

        chapter_result = scrape_bible_chapter(url)

        # Break if chapter 404s (Hit end of book)
        if chapter_result is None:
            break

        book_data["chapters"].append({
            "chapter": chapter_num,
            "title": chapter_result["chapter_title"],
            "verses": chapter_result["verses"],
        })

        print(f"  -> Processed Chapter {chapter_num}", end="\r")
        chapter_num += 1
        time.sleep(0.3)  # Gentle delay between chapters

    # Save the file only if we actually found chapters
    if book_data["chapters"]:
        filename = os.path.join(output_dir, f"{book_name_en}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(book_data, f, ensure_ascii=False, indent=2)
        print(f"\nSuccessfully saved {book_name_en}.json ({chapter_num - 1} chapters)")
        return True
    else:
        return False


# --- Main Execution Control Loop ---
if __name__ == "__main__":
    output_folder = "am_book"
    print(f"Initializing mass scrape into folder: '{output_folder}/'")
    
    # Loop from Book 1 (Genesis) through Book 39 (Malachi)
    for index, book_name in enumerate(OLD_TESTAMENT_BOOKS, start=1):
        print(f"\n[{index}/39] Processing Book: {book_name.upper()} (Code: {index:02d})...")
        
        success = scrape_full_book(book_number=index, book_name_en=book_name, output_dir=output_folder)
        
        if not success:
            print(f"Warning: No data could be downloaded for book index {index:02d} ({book_name})")
            
        # Give the server a breather between books
        time.sleep(1.5)
        
    print("\nProcessing complete! All retrieved Old Testament books are stored in the 'am_book/' directory.")