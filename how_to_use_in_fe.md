# Admin Language Management API

This document describes the admin API for adding and managing languages.

## Add Language

### Endpoint

`POST /api/admin/languages`

### Description

Create a new language record for the app.

### Request body

```json
{
  # Admin Language & Import Scripts — Frontend Guide

  This page documents admin language APIs and the available import scripts you can use from the server to populate the DB (quiz questions and bible books).

  ---

  ## Admin Language Management API

  Endpoints (admin-only):

  - `GET /api/admin/languages` — list languages
  - `POST /api/admin/languages` — create language
  - `PUT /api/admin/languages/{language_id}` — update language
  - `DELETE /api/admin/languages/{language_id}` — delete language

  ### Create language — request body

  ```json
  {
    "code": "am",
    "name": "Amharic",
    "native_name": "አማርኛ",
    "is_active": true
  }
  ```

  - `code` (string, required): Language code, e.g. `en`, `am`, `fr`
  - `name` (string, required): Display name
  - `native_name` (string, optional)
  - `is_active` (boolean, optional): defaults to `true`

  ### Update language

  All fields are optional for update. Use `PUT /api/admin/languages/{id}` with the same body fields.

  ### Responses

  - Success create: 201 with `{"success": true, "data": { ... }}`
  - Success update/delete/list: 200 with `success: true`
  - Non-admin requests: 403 with `{"success": false, "message": "Admin access required"}`

  ---

  ## Import Quiz Questions (script)

  Path: `scripts/import_questions.py`

  Purpose: import a JSON file containing quiz questions into the DB. The script will create or reuse the `Language`, `Book`, `Chapter`, `Level`, `Question`, `QuestionText`, `Option`, `OptionText`, and `Explanation` records as needed.

  Usage (from project root):

  ```bash
  python scripts/import_questions.py --file ../en_ge_q.json --lang en --book Genesis
  ```

  Flags:
  - `--file` (relative path to JSON file)
  - `--lang` (language code, default `en`)
  - `--book` (book name, default `Genesis`)

  JSON format expected (top-level):

  ```json
  {
    "questions": [
      {
        "question": "Who...",
        "verse_reference": "1:1",
        "level": 1,
        "options": { "A": "..", "B": "..", "C": ".." },
        "correct_answer": "A",
        "explanation": "..."
      }
    ]
  }
  ```

  What the script does per question:
  - Parses chapter number from `verse_reference` and creates `Chapter` if missing
  - Ensures `Language` exists for the provided `--lang`
  - Ensures `Book` exists for provided `--book`
  - Creates or finds a `Level` for numeric `level`
  - Creates `Question`, `QuestionText` (language), `Option` + `OptionText` (language), and `Explanation` (language)

  Output example:

  ```
  Imported 145 questions for book 'Genesis' and language 'en'.
  ```

  Notes and troubleshooting:
  - The script assumes `options` is a dict mapping labels (A,B,C,...) to strings. If absent, it skips options.
  - If `Language` with the code does not exist, it will be auto-created with a default name.

  ---

  ## Migrate Books (Bible structure) — script

  Path: `scripts/migrate_books.py`

  Purpose: migrate `Testament`, `Book`, `Chapter`, `Verse`, and `VerseText` from a source SQLite DB into the Django models. This script is interactive and intended for one-time data migrations.

  Important: update the `SOURCE_DB` path inside the script to point to your source SQLite file before running.

  Typical run:

  ```bash
  python scripts/migrate_books.py
  ```

  The script will prompt:
  - Continue? (yes/no)
  - Clear existing data before migration? (yes/no)

  What it migrates in order:
  1. Testaments — creates `Testament` rows
  2. Books — creates `Book` rows and links testaments
  3. Chapters — creates `Chapter` rows for each book
  4. Verses — creates `Verse` rows for each chapter
  5. VerseTexts — creates `VerseText` rows for each language found in the source DB

  It prints progress and verifies totals at the end. Example next steps after a successful run:

  ```bash
  # Start the server to test the new data
  python manage.py runserver 8009

  # Test the books by language API
  curl "http://127.0.0.1:8009/api/bible/books/by-language?language=en"
  ```

  Notes:
  - The script uses unique-name matching and `get_or_create` to avoid duplicates.
  - It will refuse to delete languages/books that have dependent data unless you explicitly confirm clearing existing data.

  ---

  If you want, I can add example frontend code snippets that call the admin APIs (language create/update) and also a small wrapper to call the `import_questions.py` via an admin-only upload endpoint. Which would you like next?
```

## Admin-only access

All `/api/admin/*` language endpoints require an authenticated admin user. If the request is not from an admin, the response will be:

```json
{
  "success": false,
  "message": "Admin access required"
}
```
