import json
import os
from pathlib import Path
import cloudinary
from cloudinary import api

# 1. Configure Cloudinary
cloudinary.config(
    cloud_name="dleykahqd",
    api_key="284571752959753",
    api_secret="B-tJyF7f1oBSt9qIulbGNvK8Hbg",
    secure=True
)

base_prefix = "bible_audio/bibel_audio/old/am/"
output_dir = Path("bible_json_data")
output_dir.mkdir(exist_ok=True)

print(f"--- Fetching ALL audio assets recursively from: {base_prefix} ---")

all_resources = []
next_cursor = None

try:
    # 2. Page loop to pull past the 500-file limitation
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
        
        print(f"Fetched {len(batch)} items... Total collected so far: {len(all_resources)}")
        
        next_cursor = response.get("next_cursor")
        if not next_cursor:
            break

    if not all_resources:
        print("❌ No files found. Verify your cloud folder contents.")
    else:
        print(f"\nProcessing {len(all_resources)} files into clean book JSONs...")
        
        books_data = {}
        
        for asset in all_resources:
            public_id = asset.get("public_id")
            res_type = asset.get("resource_type", "video")
            
            # Split path: bible_audio / bibel_audio / old / am / [book_name] / [wrong_folder] / [true_chapter_filename]
            path_parts = public_id.split('/')
            
            if len(path_parts) >= 7:
                book_name = path_parts[4].lower()      # e.g., "genesis", "hosea"
                
                # FIX: We grab the final filename segment as the true chapter indicator!
                filename = path_parts[-1] 
                
                # Safe fallback if the filename contains extension info
                true_chapter = filename.split('.')[0]  
                
                playback_url = f"https://res.cloudinary.com/dleykahqd/{res_type}/upload/{public_id}"
                
                if book_name not in books_data:
                    books_data[book_name] = {}
                
                # Map true chapter to its playback URL
                books_data[book_name][true_chapter] = playback_url

        # 3. Save each book out into its own dedicated JSON file
        for book_name, chapters in books_data.items():
            # Sort the keys numerically so Chapter 2 comes before Chapter 10
            sorted_chapters = {
                k: chapters[k] for k in sorted(chapters.keys(), key=lambda x: int(x) if x.isdigit() else x)
            }
            
            json_file_path = output_dir / f"{book_name}.json"
            
            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json.dump(sorted_chapters, json_file, indent=4, ensure_ascii=False)
                
            print(f"💾 Created: {json_file_path}")
            
        print(f"\n✅ Done! Check your '{output_dir.absolute()}' folder for all generated files.")

except Exception as e:
    print(f"An error occurred: {e}")