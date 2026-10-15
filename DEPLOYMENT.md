# 🚀 Make Your Move — Deployment Guide

> **Repo:** https://github.com/Aryan1358-ai/MAKE-YOUR-MOVE-.git
> **Stack:** Django 6 (Python) + React 19 (Vite) + PostgreSQL

This is a **full-stack app** with two separate parts that need to be deployed independently:

| Part | What | Deploy On |
|------|------|-----------|
| **Frontend** | React + Vite SPA | Vercel |
| **Backend** | Django REST API | Render / Railway |
| **Database** | PostgreSQL | Render / Railway / Supabase |

---

## 📁 Project Structure

```
MAKE-YOUR-MOVE-/
├── DJP/                  # Django project settings
│   ├── settings.py       # ⚠️ Needs production config
│   ├── urls.py
│   └── wsgi.py
├── assessment/           # Django app (all API logic)
│   ├── views.py          # Main assessment endpoints
│   ├── auth_views.py     # Auth (register/login/logout + Google OAuth)
│   ├── analytics_views.py # Admin analytics dashboard
│   ├── deep_dive.py      # Gemini AI chat logic
│   ├── models.py         # DB models
│   └── urls.py           # API routes
├── frontend/             # React app (Vite)
│   ├── src/
│   ├── .env.example      # ⚠️ Copy to .env and fill in values
│   ├── package.json
│   └── vite.config.js
├── manage.py
├── .env.example          # ⚠️ Copy to .env and fill in values
└── .env                  # ⚠️ NOT in repo — must create manually
```

---

## 🔐 Step 0: Set Up Google OAuth (Required for "Sign in with Google")

> [!IMPORTANT]
> The `.env` files are **not** included in the repo (they're in `.gitignore`). Every person who clones this repo must create their own Google OAuth credentials and `.env` files for OAuth to work.

### 0a. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown (top-left) → **New Project**
3. Name it (e.g. `MakeYourMove`) → **Create**
4. Make sure the new project is selected

### 0b. Configure the OAuth Consent Screen

1. In the left sidebar: **APIs & Services → OAuth consent screen**
2. Click **Get Started** or **Configure Consent Screen**
3. Fill in:
   - **App name:** `Make Your Move`
   - **User support email:** your email
   - **Developer contact email:** your email
4. **Audience:** Choose **External** (anyone with a Google account can sign in)
5. Click through the remaining steps (scopes — no changes needed, just continue)
6. Under **Test Users** → **Add Users** → add your own Gmail address
   > While the app is in "Testing" mode, only added test users can sign in. Publish to "Production" to allow anyone.
7. Save

### 0c. Create OAuth Client ID (Credentials)

1. Go to **APIs & Services → Credentials**
2. Click **+ CREATE CREDENTIALS → OAuth client ID**
3. **Application type:** Web application
4. **Name:** `MakeYourMove Web`
5. **Authorized JavaScript origins:**

   | Environment | Origin |
   |-------------|--------|
   | Local dev | `http://localhost:5173` |
   | Production (Vercel) | `https://your-app.vercel.app` |

6. **Authorized redirect URIs:**

   | Environment | URI |
   |-------------|-----|
   | Local dev | `http://localhost:5173` |
   | Production (Vercel) | `https://your-app.vercel.app` |

7. Click **Create**
8. **Copy the Client ID** — it looks like:
   ```
   123456789-xxxxxxxxxxxxxxx.apps.googleusercontent.com
   ```

### 0d. Add the Client ID to Your `.env` Files

**Root `.env`** (for Django backend):
```bash
cp .env.example .env
# Then edit .env and set:
GOOGLE_OAUTH_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
```

**Frontend `.env`** (for React):
```bash
cp frontend/.env.example frontend/.env
# Then edit frontend/.env and set:
VITE_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
```

> [!NOTE]
> Both files use the **same Client ID** — the frontend sends it to Google to get a token, and the backend uses it to verify that token is genuine.

### 0e. Install the Backend Dependency

The backend needs the `google-auth` library to verify tokens:
```bash
pip install google-auth
```

> [!TIP]
> If `google-auth` is already installed (it comes bundled with `google-genai`), you can skip this step.

---

## 🗄️ Step 1: Set Up PostgreSQL Database

You need a cloud PostgreSQL database. Options:

- **Render** → Free PostgreSQL (auto-expires after 90 days)
- **Railway** → Pay-per-use PostgreSQL
- **Supabase** → Free tier with 500MB
- **Neon** → Free serverless Postgres

After creating the database, note down:
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host.com
DB_PORT=5432
```

---

## ⚙️ Step 2: Deploy Backend (Django) on Render

### 2a. Prepare files

You'll need to add these files to the repo root:

**`requirements.txt`** (create this file):
```
Django==6.0.3
djangorestframework==3.17.1
django-cors-headers==4.9.0
psycopg[binary]==3.3.3
python-dotenv==1.2.2
google-genai==2.11.0
google-auth==2.40.1
gunicorn==23.0.0
whitenoise==6.9.0
```

**`Procfile`** (create this file — for Render/Railway):
```
web: gunicorn DJP.wsgi:application --bind 0.0.0.0:$PORT
```

**`runtime.txt`** (optional, pin Python version):
```
python-3.12.0
```

### 2b. Update `DJP/settings.py` for Production

These changes **MUST** be made before deploying:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# ── Database ──────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'makeyourmove'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# ── CORS (add your Vercel URL) ────────────────────────
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    os.environ.get('FRONTEND_URL', 'http://localhost:5173'),  # e.g. https://make-your-move.vercel.app
]
CORS_ALLOW_CREDENTIALS = True

# ── CSRF ──────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    os.environ.get('FRONTEND_URL', 'http://localhost:5173'),
]

# ── Session Cookies (cross-domain) ────────────────────
SESSION_COOKIE_SAMESITE = 'None'     # Required for cross-domain
SESSION_COOKIE_SECURE = True         # Required when SameSite=None
SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True

# ── Static files (whitenoise) ─────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',      # ← add this
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ── Gemini API ────────────────────────────────────────
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
GEMINI_MODEL = 'gemini-2.0-flash'

# ── Google OAuth ──────────────────────────────────────
GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
```

### 2c. Deploy on Render

1. Go to [render.com](https://render.com) → New → **Web Service**
2. Connect GitHub repo: `Aryan1358-ai/MAKE-YOUR-MOVE-`
3. Settings:
   - **Name:** `makeyourmove-api`
   - **Root Directory:** `.` (leave empty / root)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command:** `gunicorn DJP.wsgi:application --bind 0.0.0.0:$PORT`
4. Add **Environment Variables**:

| Key | Value |
|-----|-------|
| `DJANGO_SECRET_KEY` | Generate a random 50-char string |
| `DEBUG` | `False` |
| `DB_NAME` | *(from Step 1)* |
| `DB_USER` | *(from Step 1)* |
| `DB_PASSWORD` | *(from Step 1)* |
| `DB_HOST` | *(from Step 1)* |
| `DB_PORT` | `5432` |
| `GEMINI_API_KEY` | *(your Gemini API key)* |
| `GOOGLE_OAUTH_CLIENT_ID` | *(from Step 0c)* |
| `FRONTEND_URL` | *(your Vercel URL, e.g. `https://make-your-move.vercel.app`)* |
| `ALLOWED_HOSTS` | `makeyourmove-api.onrender.com` |

5. Deploy → wait for it to go live
6. Note the URL (e.g. `https://makeyourmove-api.onrender.com`)

### 2d. Create Admin User

After deployment, go to Render → Shell and run:
```bash
python manage.py createsuperuser
```
Set email `admin@makeyourmove.com` and a strong password. This user can access `/analytics`.

---

## 🖥️ Step 3: Deploy Frontend (React) on Vercel

### 3a. Update API Base URL

Edit `frontend/src/api/client.js` — change line 7:

```js
// BEFORE (localhost only):
const API_BASE = 'http://localhost:8000/api';

// AFTER (use env var with fallback):
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
```

This lets you set the backend URL via Vercel environment variables.

### 3b. Deploy on Vercel

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import GitHub repo: `Aryan1358-ai/MAKE-YOUR-MOVE-`
3. **Framework Preset:** Vite
4. **Root Directory:** `frontend`
5. **Build Command:** `npm run build`
6. **Output Directory:** `dist`
7. Add **Environment Variables**:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://makeyourmove-api.onrender.com/api` *(your Render URL + /api)* |
| `VITE_GOOGLE_CLIENT_ID` | *(same Client ID from Step 0c)* |

8. Deploy!

### 3c. Handle Client-Side Routing

Create `frontend/vercel.json` to handle React Router:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Without this, refreshing on `/login` or `/results` will show a 404.

### 3d. Update Google OAuth Origins for Production

After you get your Vercel URL, go back to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials) and add:

- **Authorized JavaScript origins:** `https://your-app.vercel.app`
- **Authorized redirect URIs:** `https://your-app.vercel.app`

> [!WARNING]
> If you skip this step, Google OAuth will work locally but fail in production with an "origin mismatch" error.

---

## 🔗 Step 4: Connect Frontend ↔ Backend

After both are deployed:

1. **Copy your Vercel URL** (e.g. `https://make-your-move.vercel.app`)
2. **Go to Render → Environment Variables** and set:
   - `FRONTEND_URL` = `https://make-your-move.vercel.app`
   - `ALLOWED_HOSTS` = `makeyourmove-api.onrender.com`
3. **Redeploy** the backend on Render

---

## 🔑 Environment Variables Summary

### Backend (Render / `.env`)
| Variable | Example | Required |
|----------|---------|----------|
| `DJANGO_SECRET_KEY` | `your-random-50-char-string` | ✅ |
| `DEBUG` | `False` | ✅ |
| `DB_NAME` | `makeyourmove_db` | ✅ |
| `DB_USER` | `makeyourmove_user` | ✅ |
| `DB_PASSWORD` | `super-secret-password` | ✅ |
| `DB_HOST` | `dpg-xxx.oregon-postgres.render.com` | ✅ |
| `DB_PORT` | `5432` | ✅ |
| `GEMINI_API_KEY` | `AQ.Ab8RN...` | ✅ |
| `GOOGLE_OAUTH_CLIENT_ID` | `578235...apps.googleusercontent.com` | ✅ for Google login |
| `FRONTEND_URL` | `https://make-your-move.vercel.app` | ✅ |
| `ALLOWED_HOSTS` | `makeyourmove-api.onrender.com` | ✅ |

### Frontend (Vercel / `frontend/.env`)
| Variable | Example | Required |
|----------|---------|----------|
| `VITE_API_URL` | `https://makeyourmove-api.onrender.com/api` | ✅ in production |
| `VITE_GOOGLE_CLIENT_ID` | `578235...apps.googleusercontent.com` | ✅ for Google login |

---

## ⚡ Quick Start (Local Development)

```bash
# 1. Clone the repo
git clone https://github.com/Aryan1358-ai/MAKE-YOUR-MOVE-.git
cd MAKE-YOUR-MOVE-

# 2. Set up backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt

# 3. Create backend .env
cp .env.example .env
# Edit .env → fill in GEMINI_API_KEY, GOOGLE_OAUTH_CLIENT_ID, DB credentials

# 4. Set up database
python manage.py migrate
python manage.py createsuperuser

# 5. Start backend
python manage.py runserver

# 6. Set up frontend (new terminal)
cd frontend
npm install

# 7. Create frontend .env
cp .env.example .env
# Edit .env → fill in VITE_GOOGLE_CLIENT_ID (same value as backend)

# 8. Start frontend
npm run dev
```

---

## ✅ Post-Deployment Checklist

- [ ] Database migrated (`python manage.py migrate`)
- [ ] Admin user created (`python manage.py createsuperuser`)
- [ ] Frontend can reach backend (test signup/login)
- [ ] CORS is working (no console errors about blocked requests)
- [ ] Session cookies are being set (check browser DevTools → Application → Cookies)
- [ ] Google OAuth works (test "Sign in with Google" button)
- [ ] Google OAuth origins updated for production URL
- [ ] Gemini deep-dive chat works (requires valid API key)
- [ ] Analytics page loads for admin users at `/analytics`

---

## 🐛 Common Issues

| Problem | Fix |
|---------|-----|
| **"Missing required parameter: client_id"** (Google OAuth) | `VITE_GOOGLE_CLIENT_ID` is missing or empty in `frontend/.env`. Create the file and add your Client ID |
| **"Google OAuth is not configured on this server"** | `GOOGLE_OAUTH_CLIENT_ID` is missing in the backend `.env` |
| **"origin_mismatch" from Google** | Your site URL isn't in the OAuth credential's Authorized JavaScript Origins. Add it in Google Cloud Console |
| **Google login works locally but not in production** | Add your production URL (Vercel) to both "Authorized JavaScript origins" and "Authorized redirect URIs" in Google Cloud Console |
| **OAuth consent screen says "unverified app"** | Normal for apps in Testing mode. Click "Continue" to proceed, or publish the app for production |
| CORS errors in browser console | Make sure `FRONTEND_URL` on Render matches your exact Vercel URL (no trailing slash) |
| 401 on every API call | Session cookies not being sent — check `SESSION_COOKIE_SAMESITE = 'None'` and `SESSION_COOKIE_SECURE = True` |
| Login works but session lost on refresh | Cookie domain mismatch — ensure `withCredentials: true` in axios and CORS is configured |
| 404 on page refresh (Vercel) | Add `vercel.json` with rewrites (see Step 3c) |
| Static files 404 on backend | Run `python manage.py collectstatic --noinput` and ensure `whitenoise` is in middleware |
| Database connection refused | Check `DB_HOST`, `DB_PORT`, and that Render can reach your Postgres instance |

---

## 📱 API Endpoints Reference

All endpoints are prefixed with `/api/`:

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/auth/register/` | POST | No | Create account |
| `/api/auth/login/` | POST | No | Login |
| `/api/auth/google/` | POST | No | Google OAuth login |
| `/api/auth/logout/` | POST | Yes | Logout |
| `/api/auth/me/` | GET | Yes | Current user info |
| `/api/session/start/` | POST | Yes | Start assessment |
| `/api/session/` | GET | Yes | Get current session |
| `/api/session/context/` | POST | Yes | Submit context intake |
| `/api/activity/<n>/submit/` | POST | Yes | Submit activity (1-6) |
| `/api/thinking-styles/` | GET | Yes | Get thinking style results |
| `/api/validation/<domain>/submit/` | POST | Yes | Submit validation |
| `/api/results/` | GET | Yes | Get final results |
| `/api/roadmap/<domain>/` | GET | Yes | Get domain roadmap |
| `/api/deep-dive/<domain>/start/` | POST | Yes | Start AI deep-dive |
| `/api/deep-dive/<domain>/message/` | POST | Yes | Send deep-dive message |
| `/api/analytics/` | GET | Admin | Analytics dashboard data |

---

*Last updated: October 15, 2026*
