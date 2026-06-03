# Admin API Documentation

**Base URL**: `https://bibel-quiz.onrender.com/api/admin`

## Authentication

### Login URL
`POST https://bibel-quiz.onrender.com/api/auth/login`

### Request body
```json
{
  "username_or_email": "admin@example.com",
  "password": "StrongPass123!"
}
```

### Successful response
```json
{
  "status": "success",
  "data": {
    "access_token": "<JWT access token>",
    "refresh_token": "<JWT refresh token>",
    "session_token": "<session token>",
    "expires_at": "2026-07-02T19:19:34.713883Z",
    "user_id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_admin": true
  }
}
```

### Usage in frontend
- Send login payload as JSON to `/api/auth/login`
- Save `data.access_token`
- Use `Authorization: Bearer <access_token>` on all admin requests

**Authentication**: All admin endpoints require JWT token in `Authorization: Bearer {access_token}` header

**Admin Requirement**: All endpoints require `is_admin=true` on user account

---

## 1. USER MANAGEMENT

### 1.1 List All Users
```
GET /api/admin/users
```

**Query Parameters:**
- `limit` (optional, default: 100): Number of users per page
- `offset` (optional, default: 0): Starting position

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/users?limit=10&offset=0"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "created_at": "2026-06-01T17:21:30.798586Z",
        "last_login": "2026-06-01T17:26:42.308256Z",
        "is_active": true,
        "is_admin": true,
        "total_quizzes_taken": 5,
        "total_correct_answers": 120,
        "total_questions_answered": 200
      }
    ],
    "total": 1,
    "limit": 10,
    "offset": 0
  }
}
```

**Error (403):**
```json
{
  "success": false,
  "message": "Admin access required"
}
```

---

### 1.2 Get User Statistics
```
GET /api/admin/users/stats
```

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/users/stats"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_users": 150,
    "total_quizzes": 1500,
    "total_questions": 15000,
    "total_correct": 12500,
    "avg_quizzes_per_user": 10.0
  }
}
```

---

### 1.3 Get Single User Details
```
GET /api/admin/users/{user_id}
```

**Path Parameters:**
- `user_id` (required): User ID to retrieve

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/users/5"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 5,
    "username": "john_doe",
    "email": "john@example.com",
    "created_at": "2026-05-15T10:00:00.000000Z",
    "last_login": "2026-06-01T14:30:00.000000Z",
    "is_active": true,
    "is_admin": false,
    "total_quizzes_taken": 25,
    "total_correct_answers": 450,
    "total_questions_answered": 600
  }
}
```

**Error (404):**
```json
{
  "success": false,
  "message": "User not found"
}
```

---

### 1.4 Update User Active Status
```
PUT /api/admin/users/{user_id}
```

**Path Parameters:**
- `user_id` (required): User ID to update

**Request Body:**
```json
{
  "is_active": false
}
```

**Request:**
```bash
curl -X PUT -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}' \
  "https://bibel-quiz.onrender.com/api/admin/users/5"
```

**Response (200):**
```json
{
  "success": true,
  "message": "User status updated"
}
```

---

### 1.5 Update User Admin Status (Promote/Demote)
```
PUT /api/admin/users/{user_id}/admin
```

**Path Parameters:**
- `user_id` (required): User ID to update

**Request Body:**
```json
{
  "is_admin": true
}
```

**Request:**
```bash
curl -X PUT -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_admin": true}' \
  "https://bibel-quiz.onrender.com/api/admin/users/5/admin"
```

**Response (200):**
```json
{
  "success": true,
  "message": "Admin status updated"
}
```

---

### 1.6 Get User Quiz Progress
```
GET /api/admin/users/{user_id}/progress
```

**Path Parameters:**
- `user_id` (required): User ID

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/users/5/progress"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "quiz_attempts": [
      {
        "id": 1,
        "book_name": "Genesis",
        "questions_count": 10,
        "correct_answers": 8,
        "taken_at": "2026-06-01T10:00:00Z",
        "score": 80
      }
    ],
    "book_progress": [
      {
        "book_id": 1,
        "book_name": "Genesis",
        "total_questions": 100,
        "answered_correctly": 75,
        "progress": 75
      }
    ],
    "total_quizzes": 25,
    "total_books_progress": 5
  }
}
```

---

## 2. BOOK MANAGEMENT

### 2.1 List All Books
```
GET /api/admin/books
```

**Query Parameters:**
- `testament` (optional): Filter by "Old" or "New"

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/books?testament=Old"
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Genesis",
      "testament": "Old",
      "chapters": 50,
      "verses": 1533
    },
    {
      "id": 2,
      "name": "Exodus",
      "testament": "Old",
      "chapters": 40,
      "verses": 1213
    }
  ]
}
```

---

### 2.2 Create a Book
```
POST /api/admin/books
```

**Request Body:**
```json
{
  "name": "New Book Name",
  "testament": "Old"
}
```

**Request:**
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Book", "testament": "Old"}' \
  "https://bibel-quiz.onrender.com/api/admin/books"
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 67,
    "name": "New Book",
    "testament": "Old",
    "chapters": 0,
    "verses": 0
  }
}
```

**Error (400):**
```json
{
  "success": false,
  "errors": {
    "name": ["This field may not be blank."],
    "testament": ["This field may not be blank."]
  }
}
```

---

### 2.3 Get Single Book
```
GET /api/admin/books/{book_id}
```

**Path Parameters:**
- `book_id` (required): Book ID

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/books/1"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Genesis",
    "testament": "Old",
    "chapters": 50,
    "verses": 1533
  }
}
```

---

### 2.4 Update Book
```
PUT /api/admin/books/{book_id}
```

**Path Parameters:**
- `book_id` (required): Book ID

**Request Body:**
```json
{
  "name": "Updated Book Name",
  "testament": "Old"
}
```

**Request:**
```bash
curl -X PUT -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Genesis"}' \
  "https://bibel-quiz.onrender.com/api/admin/books/1"
```

**Response (200):**
```json
{
  "success": true,
  "message": "Book updated successfully"
}
```

---

### 2.5 Delete Book
```
DELETE /api/admin/books/{book_id}
```

**Path Parameters:**
- `book_id` (required): Book ID

**Request:**
```bash
curl -X DELETE -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/books/1"
```

**Response (200):**
```json
{
  "success": true,
  "message": "Book deleted successfully"
}
```

---

## 3. LANGUAGE MANAGEMENT

### 3.1 List All Languages
```
GET /api/admin/languages
```

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/languages"
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "code": "en",
      "name": "English",
      "native_name": null,
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "code": "am",
      "name": "Amharic",
      "native_name": "አማርኛ",
      "is_active": true,
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

---

### 3.2 Create a Language
```
POST /api/admin/languages
```

**Request Body:**
```json
{
  "code": "fr",
  "name": "French",
  "native_name": "Français"
}
```

**Request:**
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "fr", "name": "French", "native_name": "Français"}' \
  "https://bibel-quiz.onrender.com/api/admin/languages"
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "code": "fr",
    "name": "French",
    "native_name": "Français",
    "is_active": true,
    "created_at": "2026-06-01T17:30:00Z"
  }
}
```

---

### 3.3 Update Language
```
PUT /api/admin/languages/{language_id}
```

**Path Parameters:**
- `language_id` (required): Language ID

**Request Body:**
```json
{
  "name": "Updated Name",
  "native_name": "Updated Native",
  "is_active": true
}
```

**Request:**
```bash
curl -X PUT -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}' \
  "https://bibel-quiz.onrender.com/api/admin/languages/3"
```

**Response (200):**
```json
{
  "success": true,
  "message": "Language updated successfully"
}
```

---

### 3.4 Delete Language
```
DELETE /api/admin/languages/{language_id}
```

**Path Parameters:**
- `language_id` (required): Language ID

**Request:**
```bash
curl -X DELETE -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/languages/3"
```

**Response (200):**
```json
{
  "success": true,
  "message": "Language deleted successfully"
}
```

---

## 4. BIBLE IMPORT

### 4.1 Get Bible Import Status
```
GET /api/admin/import/bible
```

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/import/bible"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "books_imported": 66,
    "verses_imported": 31102,
    "verse_texts_by_language": {
      "en": 31102,
      "am": 31102
    },
    "languages_available": ["en", "am"]
  }
}
```

---

### 4.2 Import Bible File
```
POST /api/admin/import/bible
```

**Request Body:**
```json
{
  "file_path": "bibel_txt/new/en/genesis.txt",
  "language": "en"
}
```

**Request:**
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "bibel_txt/new/en/1_Corinthians.txt", "language": "en"}' \
  "https://bibel-quiz.onrender.com/api/admin/import/bible"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "Bible imported successfully",
    "book_name": "1 Corinthians",
    "verses_imported": 437,
    "language": "en"
  }
}
```

**Error (400):**
```json
{
  "success": false,
  "message": "File not found or invalid format"
}
```

---

## 5. QUESTIONS IMPORT

### 5.1 Get Questions Import Status
```
GET /api/admin/import/questions
```

**Request:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://bibel-quiz.onrender.com/api/admin/import/questions"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_questions": 500,
    "questions_by_language": {
      "en": 250,
      "am": 250
    }
  }
}
```

---

### 5.2 Import Questions JSON File
```
POST /api/admin/import/questions
```

**Request Body:**
```json
{
  "file_path": "en_ge_q.json",
  "language": "en"
}
```

**File Format (en_ge_q.json):**
```json
{
  "questions": [
    {
      "question_text": "What is the first book of the Bible?",
      "book_id": 1,
      "chapter": 1,
      "verse": 1,
      "options": [
        "Genesis",
        "Exodus",
        "Leviticus",
        "Numbers"
      ],
      "correct_answer": 0
    }
  ]
}
```

**Request:**
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "en_ge_q.json", "language": "en"}' \
  "https://bibel-quiz.onrender.com/api/admin/import/questions"
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "Questions imported successfully",
    "questions_imported": 100,
    "language": "en"
  }
}
```

---

## Common Error Responses

### 401 Unauthorized (Missing/Invalid Token)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden (Not Admin)
```json
{
  "success": false,
  "message": "Admin access required"
}
```

### 404 Not Found
```json
{
  "success": false,
  "message": "Resource not found"
}
```

### 400 Bad Request
```json
{
  "success": false,
  "errors": {
    "field_name": ["Error message"]
  }
}
```

---

## Complete Example: Admin Testing Script

See [scripts/test_admin_apis.py](scripts/test_admin_apis.py) for a complete testing script.

**Run tests:**
```bash
python scripts/test_admin_apis.py --password StrongPass123!
```

**Against custom URL:**
```bash
python scripts/test_admin_apis.py --base-url http://localhost:8000 --password StrongPass123!
```

---

## Authentication Flow

1. **Login First**
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"username_or_email": "admin", "password": "StrongPass123!"}' \
     "https://bibel-quiz.onrender.com/api/auth/login"
   ```

2. **Get Access Token from Response**
   ```json
   {
     "status": "success",
     "message": "Login successful",
     "data": {
       "access_token": "eyJhbGciOiJIUzI1NiIs...",
       "user_id": 1,
       "username": "admin",
       "email": "admin@example.com",
       "is_admin": true
     }
   }
   ```

3. **Use Token in Admin Requests**
   ```bash
   curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
     "https://bibel-quiz.onrender.com/api/admin/users"
   ```

---
