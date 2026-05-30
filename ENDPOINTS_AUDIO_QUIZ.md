# Audio and Quiz Progress Endpoints

**Base URL:** `https://bibel-quiz.onrender.com/api`

**Authentication:** All progress endpoints require JWT Bearer token
```
Authorization: Bearer <access_token>
```

---

## 📻 AUDIO PROGRESS ENDPOINTS

### 1. Get User Audio Progress for a Book
**Get the user's audio listening progress for a specific book**

```
GET /user/audio/progress/<book_id>
Authorization: Bearer <access_token>
```

**URL Parameters:**
- `book_id` (integer, required) - The book ID

**Query Parameters:**
- None

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "book_id": 1,
    "book_name": "Genesis",
    "testament": "Old",
    "current_chapter": 3,
    "current_verse": 15,
    "audio_current_position": 450,
    "audio_completed_chapters": [1, 2],
    "total_audio_duration": 7200,
    "listened_audio_duration": 2700,
    "remaining_audio_duration": 4500,
    "audio_progress_percentage": 37,
    "completed": false,
    "progress_percentage": 33
  }
}
```

**Field Descriptions:**
- `book_id` - The ID of this book
- `book_name` - Name of the book (e.g., Genesis, Exodus)
- `testament` - Old or New testament
- `current_chapter` - Which chapter user is currently on
- `current_verse` - Which verse in the current chapter
- `audio_current_position` - Current playback position in seconds
- `audio_completed_chapters` - Array of completed chapter numbers
- `total_audio_duration` - Total book audio in seconds
- `listened_audio_duration` - Total seconds listened
- `remaining_audio_duration` - Seconds left to listen
- `audio_progress_percentage` - Percentage of book listened (0-100)
- `completed` - If entire book is completed
- `progress_percentage` - Overall progress percentage

**cURL Example:**
```bash
curl -X GET "https://bibel-quiz.onrender.com/api/user/audio/progress/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

### 2. Update User Audio Progress for a Book
**Update the user's audio listening position and completed chapters**

```
POST /user/audio/progress/<book_id>/update
Authorization: Bearer <access_token>
Content-Type: application/json
```

**URL Parameters:**
- `book_id` (integer, required) - The book ID

**Request Body:**
```json
{
  "chapter_number": 3,
  "current_position": 450,
  "completed_chapter": 2
}
```

**Request Fields:**
- `chapter_number` (integer, required) - Current chapter user is on
- `current_position` (integer, optional) - Current playback position in seconds
- `completed_chapter` (integer, optional) - If user just finished a chapter, provide the chapter number

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "book_id": 1,
    "book_name": "Genesis",
    "testament": "Old",
    "success": true,
    "current_chapter": 3,
    "current_position": 450,
    "audio_completed_chapters": [1, 2],
    "audio_progress_percentage": 37,
    "total_audio_duration": 7200,
    "listened_audio_duration": 2700,
    "remaining_audio_duration": 4500
  }
}
```

**Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "chapter_number is required"
}
```

**cURL Example:**
```bash
curl -X POST "https://bibel-quiz.onrender.com/api/user/audio/progress/1/update" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "chapter_number": 3,
    "current_position": 450,
    "completed_chapter": 2
  }'
```

---

## 🎯 QUIZ PROGRESS ENDPOINTS

### 3. Get User Quiz Progress for a Book
**Get user's quiz progress/history for a specific book**

```
GET /user/quiz-progress/<book_id>
Authorization: Bearer <access_token>
```

**URL Parameters:**
- `book_id` (integer, required) - The book ID

**Query Parameters:**
- None

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "book_id": 1,
    "book_name": "Genesis",
    "testament": "Old",
    "total_quizzes_taken": 3,
    "completed_quizzes": 2,
    "in_progress_attempt_id": 45,
    "status": "in_progress",
    "total_questions": 10,
    "answered_questions": 7,
    "correct_answers": 5,
    "score_percentage": 71.43,
    "progress_percentage": 70,
    "can_resume": true,
    "resume_data": {
      "current_question_index": 7,
      "current_index": 7
    },
    "last_attempt_at": "2026-05-30T10:15:00Z"
  }
}
```

**Field Descriptions:**
- `book_id` - The book ID
- `book_name` - Name of the book
- `testament` - Old or New testament
- `total_quizzes_taken` - Total quiz attempts for this book
- `completed_quizzes` - Number of completed quizzes
- `in_progress_attempt_id` - ID of current attempt (if in progress)
- `status` - Current attempt status: `in_progress`, `completed`, `abandoned`
- `total_questions` - Total questions in current/last attempt
- `answered_questions` - Questions answered so far
- `correct_answers` - Correct answers in current/last attempt
- `score_percentage` - Score as percentage (0-100)
- `progress_percentage` - Progress through current attempt (0-100)
- `can_resume` - If user can resume an in-progress quiz
- `resume_data` - Data for resuming (question index, etc)
- `last_attempt_at` - When the last attempt started

**Response when no quiz progress exists:**
```json
{
  "status": "success",
  "data": {
    "book_id": 5,
    "book_name": "Exodus",
    "testament": "Old",
    "total_quizzes_taken": 0,
    "completed_quizzes": 0,
    "in_progress_attempt_id": null,
    "status": null,
    "total_questions": 0,
    "answered_questions": 0,
    "correct_answers": 0,
    "score_percentage": 0.0,
    "progress_percentage": 0,
    "can_resume": false,
    "resume_data": null,
    "last_attempt_at": null
  }
}
```

**cURL Example:**
```bash
curl -X GET "https://bibel-quiz.onrender.com/api/user/quiz-progress/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 🎓 QUIZ ACTION ENDPOINTS (For Reference)

### 4. Start a New Quiz
**Start a new quiz session for a book**

```
POST /user/quiz/start
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "book_id": 1,
  "level_id": 1,
  "language_id": 1,
  "total_questions": 10
}
```

**Request Fields:**
- `book_id` (integer, required) - Book to quiz on
- `level_id` (integer, optional) - Difficulty level
- `language_id` (integer, optional) - Language for quiz
- `total_questions` (integer, optional, default: 10) - Number of questions

**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "attempt_id": 45,
    "book_name": "Genesis",
    "testament": "Old",
    "total_questions": 10,
    "status": "in_progress",
    "started_at": "2026-05-30T10:15:00Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST "https://bibel-quiz.onrender.com/api/user/quiz/start" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 1,
    "level_id": 1,
    "language_id": 1,
    "total_questions": 10
  }'
```

---

### 5. Submit Quiz Answer
**Submit answer for current question**

```
POST /user/quiz/submit-answer
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "attempt_id": 45,
  "question_id": 123,
  "selected_option": "A"
}
```

**Request Fields:**
- `attempt_id` (integer, required) - Quiz attempt ID
- `question_id` (integer, required) - Question being answered
- `selected_option` (string, required) - Selected option (A, B, C, D)

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "is_correct": true,
    "score_percentage": 75.5,
    "answered_questions": 8,
    "progress_percentage": 80
  }
}
```

**cURL Example:**
```bash
curl -X POST "https://bibel-quiz.onrender.com/api/user/quiz/submit-answer" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "attempt_id": 45,
    "question_id": 123,
    "selected_option": "A"
  }'
```

---

### 6. Complete Quiz
**Mark quiz as completed and get final score**

```
POST /user/quiz/complete
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "attempt_id": 45
}
```

**Request Fields:**
- `attempt_id` (integer, required) - Quiz attempt ID to complete

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "attempt_id": 45,
    "book_name": "Genesis",
    "status": "completed",
    "total_questions": 10,
    "correct_answers": 8,
    "score_percentage": 80.0,
    "completed_at": "2026-05-30T10:25:00Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST "https://bibel-quiz.onrender.com/api/user/quiz/complete" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "attempt_id": 45
  }'
```

---

## 📊 COMBINED BOOK PROGRESS

### 7. Get All Book Progress (Audio + Reading + Quiz)
**Get user's complete progress through all books**

```
GET /user/book-progress
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": [
    {
      "book_id": 1,
      "book_name": "Genesis",
      "testament": "Old",
      "current_chapter": 3,
      "current_verse": 15,
      "questions_answered": 45,
      "correct_answers": 38,
      "audio_started": true,
      "audio_can_resume": true,
      "audio_current_position": 450,
      "audio_completed_chapters": [1, 2],
      "audio_progress_percentage": 37,
      "total_audio_chapters": 50,
      "quiz_in_progress": true,
      "quiz_resume_attempt_id": 45,
      "quiz_resume_status": "in_progress",
      "quiz_resume_total_questions": 10,
      "quiz_resume_answered_questions": 7,
      "quiz_resume_correct_answers": 5,
      "quiz_resume_score_percentage": 71.43,
      "quiz_resume_progress_percentage": 70,
      "last_activity": "2026-05-30T10:25:00Z",
      "completed": false
    },
    {
      "book_id": 2,
      "book_name": "Exodus",
      "testament": "Old",
      "current_chapter": 1,
      "current_verse": 1,
      "questions_answered": 0,
      "correct_answers": 0,
      "audio_started": false,
      "audio_can_resume": false,
      "audio_current_position": 0,
      "audio_completed_chapters": [],
      "audio_progress_percentage": 0,
      "total_audio_chapters": 40,
      "quiz_in_progress": false,
      "quiz_resume_attempt_id": null,
      "quiz_resume_status": null,
      "quiz_resume_total_questions": 0,
      "quiz_resume_answered_questions": 0,
      "quiz_resume_correct_answers": 0,
      "quiz_resume_score_percentage": 0.0,
      "quiz_resume_progress_percentage": 0,
      "last_activity": null,
      "completed": false
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "https://bibel-quiz.onrender.com/api/user/book-progress" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 🧭 Frontend Profile Page Usage

Use `GET /user/book-progress` to render the user's book-level progress list. Each book item now contains:
- `book_id`, `book_name`, `testament` — identify the book
- `audio_started` — whether audio listening has begun
- `audio_can_resume` — whether audio is started but not completed
- `audio_progress_percentage` — progress bar value for audio
- `quiz_in_progress` — whether a quiz attempt exists for the book
- `quiz_resume_attempt_id` / `quiz_resume_status` — resume button data
- `quiz_resume_progress_percentage` — quiz progress bar value

### Suggested UI behavior
- Show a book card for each entry in `book_progress`
- If `audio_started` is true, display the audio progress bar using `audio_progress_percentage`
- If `audio_can_resume` is true, show an "Resume Audio" button linking to `GET /user/audio/progress/<book_id>`
- If `quiz_in_progress` is true, show an "Resume Quiz" button using `quiz_resume_attempt_id`
- For quiz details, call `GET /user/quiz-progress/<book_id>` when the book is selected
- For audio details, call `GET /user/audio/progress/<book_id>` when the user wants to resume or inspect progress

### Example book card state
- Book: Genesis
- Audio progress: 37% (show progress bar)
- Audio resume: visible if `audio_can_resume` is true
- Quiz progress: 70% (show progress bar)
- Quiz resume: visible if `quiz_in_progress` is true

---

## 🔑 Authentication

### Get JWT Token (Login)
```
POST /auth/login
Content-Type: application/json
```

**Request:**
```json
{
  "username": "user@example.com",
  "password": "your_password"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "user_id": 123,
    "username": "user@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**cURL Example:**
```bash
curl -X POST "https://bibel-quiz.onrender.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "your_password"
  }'
```

---

## ⚠️ Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created (for start quiz) |
| 400 | Bad Request (missing/invalid fields) |
| 401 | Unauthorized (missing/invalid token) |
| 404 | Not Found |
| 500 | Server Error |

---

## 📝 Notes

- All timestamps are in ISO 8601 format (UTC)
- Durations are in seconds
- Percentages are 0-100 scale
- Audio progress is updated real-time when user is listening
- Quiz progress is only tracked after quiz is started
- Users cannot see progress without authentication
