# Bibel API — User Documentation

Base URL: `https://bibel-quiz.onrender.com`

This file contains concise sample requests and responses for the public (non-admin) Bibel APIs used by the frontend.

---

## Authentication

### Login
POST `/api/auth/login`

Request JSON:
```json
{
  "username_or_email": "admin@example.com",
  "password": "StrongPass123!"
}
```

Success (200):
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

Error (401):
```json
{
  "status": "error",
  "message": "Invalid credentials"
}
```

---

### Register
POST `/api/auth/register`

Request JSON:
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "UserPass123",
  "confirm_password": "UserPass123"
}
```

Success (201):
```json
{
  "status": "success",
  "message": "User registered successfully.",
  "data": {
    "id": 42,
    "username": "newuser",
    "email": "newuser@example.com"
  }
}
```

---

## Public Content APIs

These endpoints are for regular users. Protected endpoints require `Authorization: Bearer <access_token>`.

### List books
GET `/api/books`

Response (200):
```json
{
  "success": true,
  "data": [
    {"id":1,"name":"Genesis","testament":"Old","chapters":50,"verses":1533},
    {"id":40,"name":"Matthew","testament":"New","chapters":28,"verses":1071}
  ]
}
```

### Get languages
GET `/api/languages`

Response (200):
```json
{
  "success": true,
  "data": [
    {"id":1,"code":"en","name":"English","native_name":"English","is_active":true},
    {"id":2,"code":"am","name":"Amharic","native_name":"አማርኛ","is_active":true}
  ]
}
```

### Get chapters for a book
GET `/api/books/{book_id}/chapters`

Response (200):
```json
{
  "success": true,
  "data": [
    {"chapter":1,"verses":31},
    {"chapter":2,"verses":25}
  ]
}
```

### Get verses for a chapter
GET `/api/books/{book_id}/chapters/{chapter}/verses`

Response (200):
```json
{
  "success": true,
  "data": [
    {"verse":1,"text":"In the beginning..."},
    {"verse":2,"text":"And the earth was..."}
  ]
}
```

---

## Quiz APIs (examples)

### Start quiz / create attempt
POST `/api/quiz/start`

Request JSON:
```json
{
  "book_id": 1,
  "language": "en",
  "num_questions": 10
}
```

Success (201):
```json
{
  "success": true,
  "data": {
    "attempt_id": 123,
    "questions": [{"id":987,"text":"What is...","choices":["A","B","C"],"correct_choice":null}],
    "started_at": "2026-06-03T12:00:00Z"
  }
}
```

### Submit answer
POST `/api/quiz/{attempt_id}/answer`

Request JSON:
```json
{
  "question_id": 987,
  "selected_choice": "A"
}
```

Response (200):
```json
{
  "success": true,
  "data": {"question_id":987,"is_correct":true,"correct_choice":"A","score":1}
}
```

---

## User profile

### Get current user
GET `/api/user/me`
Headers: `Authorization: Bearer <access_token>`

Response (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "created_at": "2026-05-28T12:00:00Z",
    "last_login": "2026-06-03T12:10:00Z",
    "is_admin": true
  }
}
```

---

If you want this file adjusted to match specific endpoint names or to include request query parameters, tell me which endpoints to focus on and I'll update it.
