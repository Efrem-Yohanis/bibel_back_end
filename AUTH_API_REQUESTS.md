# Bible Quiz Auth API

## Register user

**Endpoint**
- `POST /api/auth/register`

**Request**
```json
{
  "username": "efrem_test_user_01",
  "email": "efremyohanis116@gmail.com",
  "password": "StrongPass123!",
  "confirm_password": "StrongPass123!"
}
```

**Response**
```json
{
  "status": "success",
  "message": "User registered successfully.",
  "data": {
    "id": 123,
    "username": "efrem_test_user_01",
    "email": "efremyohanis116@gmail.com"
  }
}
```

## Forgot password

**Endpoint**
- `POST /api/auth/forgot-password`

**Request**
```json
{
  "email": "efremyohanis116@gmail.com"
}
```

**Response**
```json
{
  "status": "success",
  "message": "If an account with that email exists, a password reset request has been received."
}
```

## Login

**Endpoint**
- `POST /api/auth/login`

**Request**
```json
{
  "username_or_email": "efremyohanis116@gmail.com",
  "password": "StrongPass123!"
}
```

**Response**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "session_token": "random-session-token",
    "expires_at": "2026-06-02T10:00:00Z",
    "user_id": 123,
    "username": "efrem_test_user_01",
    "email": "efremyohanis116@gmail.com",
    "is_admin": false
  }
}
```

## Notes

- Email verification is not required for registration.
- The frontend should not call `verify-email` or `send-verification-code`.
- Login should not be blocked because of email verification.
- `forgot-password` should return success even if the email is not registered.
