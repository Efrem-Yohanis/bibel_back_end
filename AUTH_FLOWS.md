# Auth Flows: Change Password, Edit Profile, Forgot Password

**Base URL:** `https://bibel-quiz.onrender.com/api` (or `http://localhost:8000/api` locally)

---

## 1️⃣ CHANGE PASSWORD (Authenticated)

**Endpoint:** `POST /user/change-password`
**Auth:** Required (JWT Bearer token)

### Request
```json
{
  "old_password": "current_password_123",
  "new_password": "new_secure_password",
  "confirm_password": "new_secure_password"
}
```

### Response (200 OK)
```json
{
  "status": "success",
  "message": "Password changed successfully"
}
```

### Error Responses
```json
// Old password incorrect
{
  "status": "error",
  "message": "Old password is incorrect"
}

// Passwords don't match
{
  "status": "error",
  "errors": {
    "confirm_password": ["Passwords do not match"]
  }
}
```

### cURL Example
```bash
curl -X POST "http://localhost:8000/api/user/change-password" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "current_password_123",
    "new_password": "new_secure_password",
    "confirm_password": "new_secure_password"
  }'
```

---

## 2️⃣ EDIT PROFILE (Authenticated)

**Endpoint:** `PUT /user/profile`
**Auth:** Required (JWT Bearer token)

### Request (Update username)
```json
{
  "username": "new_username"
}
```

### Request (Update email)
```json
{
  "email": "newemail@example.com"
}
```

### Request (Update both)
```json
{
  "username": "new_username",
  "email": "newemail@example.com"
}
```

### Response (200 OK)
```json
{
  "status": "success",
  "message": "Profile updated successfully",
  "data": {
    "id": 123,
    "username": "new_username",
    "email": "newemail@example.com"
  }
}
```

### Error Responses
```json
// Username already taken
{
  "status": "error",
  "message": "Username already taken"
}

// Email already registered
{
  "status": "error",
  "message": "Email already registered"
}
```

### cURL Example
```bash
curl -X PUT "http://localhost:8000/api/user/profile" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_username",
    "email": "newemail@example.com"
  }'
```

---

## 3️⃣ FORGOT PASSWORD FLOW (Public)

### Step 1: Request Password Reset
**Endpoint:** `POST /auth/forgot-password`
**Auth:** Not required (AllowAny)

#### Request
```json
{
  "email": "user@example.com"
}
```

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Password reset token generated",
  "reset_token": "NKkXp-6J2YlDhV7qZ4wP8L9m5B0c3E1fG2J4k6R8s0T2v4"
}
```

⚠️ **CURRENT BEHAVIOR:** Token is returned in response. 
📧 **RECOMMENDED:** Send token via email to user instead.

#### Error Response
```json
{
  "status": "error",
  "message": "User with that email does not exist"
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com"
  }'
```

---

### Step 2: Reset Password with Token
**Endpoint:** `POST /auth/reset-password`
**Auth:** Not required (AllowAny)

#### Request
```json
{
  "token": "NKkXp-6J2YlDhV7qZ4wP8L9m5B0c3E1fG2J4k6R8s0T2v4",
  "new_password": "new_secure_password",
  "confirm_password": "new_secure_password"
}
```

#### Response (200 OK)
```json
{
  "status": "success",
  "message": "Password reset successful",
  "data": {
    "user_id": 123,
    "username": "john_doe"
  }
}
```

#### Error Responses
```json
// Token expired (1 hour expiration)
{
  "status": "error",
  "message": "Reset token has expired"
}

// Invalid token
{
  "status": "error",
  "message": "Invalid or expired reset token"
}

// Passwords don't match
{
  "status": "error",
  "errors": {
    "confirm_password": ["Passwords do not match"]
  }
}
```

#### cURL Example
```bash
curl -X POST "http://localhost:8000/api/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "NKkXp-6J2YlDhV7qZ4wP8L9m5B0c3E1fG2J4k6R8s0T2v4",
    "new_password": "new_secure_password",
    "confirm_password": "new_secure_password"
  }'
```

---

## 🎯 Frontend Implementation Guide

### Change Password Page Flow
1. User clicks "Change Password"
2. Show form with fields:
   - `old_password` (input type="password")
   - `new_password` (input type="password")
   - `confirm_password` (input type="password")
3. Validate:
   - new_password and confirm_password match
   - new_password is at least 6 characters
4. POST to `/api/user/change-password`
5. Show success/error message
6. On success, optionally log user out (require re-login with new password)

### Edit Profile Page Flow
1. User clicks "Edit Profile"
2. Show form with fields:
   - `username` (optional)
   - `email` (optional)
3. Pre-fill current values
4. Validate:
   - username not empty if changed
   - email valid format if changed
5. PUT to `/api/user/profile`
6. Show success/error message
7. On success, update stored user data and display

### Forgot Password Page Flow

#### Page 1: Email Entry
1. User clicks "Forgot Password"
2. Show form with field:
   - `email` (input type="email")
3. POST to `/api/auth/forgot-password`
4. On success:
   - Show message: "Check your email for reset instructions"
   - Navigate to reset password page
   - **OR** if using frontend-returned token:
     - Save token temporarily
     - Show reset form immediately
5. On error (email not found):
   - Show: "Email not found in system"
   - Link to registration page

#### Page 2: Reset Password
1. If you received token from frontend:
   - Token is already available
2. If using email flow:
   - User clicks link in email (backend generates reset link)
   - Extract token from URL: `/reset-password?token=...`
3. Show form with fields:
   - `new_password` (input type="password")
   - `confirm_password` (input type="password")
4. Validate:
   - Both passwords match
   - Password at least 6 characters
5. POST to `/api/auth/reset-password` with:
   - token (from URL or state)
   - new_password
   - confirm_password
6. On success:
   - Show: "Password reset successfully! Redirecting to login..."
   - Redirect to login page after 2-3 seconds
7. On error:
   - If token expired: Show link to request new token
   - If invalid token: Show link back to forgot password

---

## 🔒 Security Notes

- **Token Expiration:** 1 hour (3600 seconds)
- **Passwords:** Never store or log passwords
- **Change Password:** Requires old password verification
- **Reset Password:** Uses time-limited token
- **HTTPS:** Always use HTTPS in production
- **Rate Limiting:** Recommended to limit forgot-password requests (e.g., 3 per hour per IP)

---

## 📊 Status Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Change Password | ✅ Implemented | Works, requires auth |
| Edit Profile | ✅ Implemented | Works, requires auth |
| Forgot Password | ✅ Implemented | Works, token in response |
| Reset Password | ✅ Implemented | Works, token expires in 1 hour |
| Email Sending | ❌ Not Integrated | Token returned in API response instead |

---

## 📧 TODO: Email Integration

To send reset links via email instead of returning token in response, add:

1. **Install packages**
   ```
   pip install django-anymail
   ```

2. **Configure email in settings.py**
   ```python
   EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
   ANYMAIL = {
       "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY"),
   }
   DEFAULT_FROM_EMAIL = "noreply@bibel-quiz.com"
   ```

3. **Update ForgotPasswordView to send email**
   ```python
   from django.core.mail import send_mail
   
   reset_token, error = auth_service.set_password_reset_token(email)
   if not error:
       reset_url = f"https://your-frontend.com/reset-password?token={reset_token}"
       send_mail(
           "Password Reset Request",
           f"Click here to reset: {reset_url}",
           "noreply@bibel-quiz.com",
           [email],
       )
   ```

---

## 💡 Recommended Frontend Workflow

```
Login Page
  ↓
[Forgot Password?] link
  ↓
Forgot Password Page (Email Input)
  ↓
Reset Password Page (Token + New Password)
  ↓
Success → Login Page
  ↓
Settings/Profile Page
  ↓
[Change Password] / [Edit Profile]
```
