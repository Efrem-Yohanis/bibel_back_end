# Render Deployment Guide

## Overview
This guide walks through deploying the Bibel Backend to Render with automatic admin user creation.

---

## Prerequisites
- Render.com account (free tier works for testing)
- GitHub repository connected to Render
- PostgreSQL database (Render provides one)

---

## Step 1: Create a Web Service on Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. **Connect your repository** (GitHub)
4. Select the `bibel_back_end` repository
5. Configure:
   - **Name**: `bibel-quiz-api` (or your choice)
   - **Region**: Choose closest to your users
   - **Runtime**: `Python 3.11`
   - **Build Command**: `bash render-build.sh`
   - **Start Command**: `gunicorn bibel_project.wsgi:application --bind 0.0.0.0:$PORT`

---

## Step 2: Create PostgreSQL Database

1. In Render Dashboard, click **New +** → **PostgreSQL**
2. Configure:
   - **Name**: `bibel-quiz-db`
   - **PostgreSQL Version**: 15 (or latest)
   - **Region**: Same as web service
3. Click **Create Database**
4. Copy the **Internal Database URL** (you'll need this)

---

## Step 3: Configure Environment Variables

In Render Dashboard → Your Web Service → **Environment**:

### Required Variables:
```
DATABASE_URL=<internal-database-url-from-step-2>
DEBUG=False
SECRET_KEY=<generate-long-random-string>
ALLOWED_HOSTS=bibel-quiz-api.onrender.com
```

### Admin User Variables (Optional - uses defaults if not set):
```
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=StrongPass123!
DEFAULT_ADMIN_FIRST_NAME=Admin
DEFAULT_ADMIN_LAST_NAME=User
```

**Note:** To generate `SECRET_KEY`, run locally:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Step 4: Connect Database to Web Service

1. In Web Service → **Environment** tab
2. Under "Database", select the PostgreSQL service you created
3. Verify `DATABASE_URL` is populated automatically

---

## Step 5: Deploy

1. Click **Deploy** button
2. Watch the build logs to verify:
   - ✓ Dependencies installed
   - ✓ Migrations ran
   - ✓ Admin user created: `✓ Created admin user: admin@example.com`
   - ✓ Static files collected

---

## Step 6: Verify Admin User

After successful deployment:

```bash
# Get your API URL from Render (e.g., https://bibel-quiz-api.onrender.com)

# Login as admin
curl -X POST https://bibel-quiz-api.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin@example.com","password":"StrongPass123!"}'

# Should return:
# {
#   "status": "success",
#   "data": {
#     "access_token": "...",
#     "user_id": 1,
#     "email": "admin@example.com",
#     "is_admin": true
#   }
# }
```

---

## Troubleshooting

### Build script not running?
- Ensure `render-build.sh` is in repo root
- File must be executable: `chmod +x render-build.sh`
- Check build logs for errors

### Admin user not created?
- Check **Deploy Logs** → **Build** for `create_default_admin` output
- Verify `DATABASE_URL` is set correctly
- Try re-running build: click **Deploy** → **Clear Build Cache** → **Deploy**

### Database connection error?
- Verify `DATABASE_URL` env var matches Render's internal database URL
- Use **Internal Database URL**, not external URL
- Wait 30 seconds after database creation before deploying web service

### 500 errors after deploy?
- Check **Runtime Logs** for stack traces
- Verify all required env vars are set
- Ensure `DEBUG=False` and `SECRET_KEY` is long/random

---

## Updating Admin Password After Deployment

After first login, change the admin password via the admin panel or run:

```bash
# Using Render CLI or SSH
python manage.py shell
>>> from core.models import User
>>> u = User.objects.get(email='admin@example.com')
>>> u.set_password('NewSecurePassword123!')
>>> u.save()
```

Or update the environment variables and re-deploy:
```
DEFAULT_ADMIN_PASSWORD=NewSecurePassword123!
```
Then click **Deploy** again.

---

## Next Steps

1. Test admin endpoints: See [ADMIN_API_REFERENCE.md](ADMIN_API_REFERENCE.md)
2. Configure custom domain (Render → Settings → Custom Domain)
3. Set up SSL/TLS (automatic on Render)
4. Enable auto-deploy on git push (Render Settings → Auto Deploy)

---

## Commands Reference

### Local testing before Render:
```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py create_default_admin

# Test login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"admin@example.com","password":"StrongPass123!"}'
```

---
