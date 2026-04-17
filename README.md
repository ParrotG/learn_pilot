# LearnPilot

Welcome to LearnPilot, my course project for **Topic 2: Personal Assistant-as-a-Service**. I designed it as a student-focused web application that turns academic PDFs into something immediately useful: structured notes, candidate deadlines, Google Calendar events, and optional Google Drive archives.

If you are a student, evaluator, or teammate looking at this repository for the first time, this guide will help you understand what LearnPilot does, how it is organized, and how to run it locally from end to end.

## What LearnPilot Does

LearnPilot is built for documents such as:

- course syllabi
- assignment briefs
- lecture notes
- announcements

After a user uploads a text-based PDF, LearnPilot can:

- extract the text from the document
- analyze it with an LLM
- generate a concise summary
- identify key study points and action items
- extract candidate schedule events for review
- create approved events in Google Calendar
- archive the original PDF to Google Drive

The backend follows a service-oriented structure, while the frontend presents the experience as a clean student productivity dashboard.

## Current Project Status

At this stage, the repository contains:

- a working FastAPI backend MVP
- a working Next.js frontend MVP
- SQLite-based local persistence
- Google OAuth, Calendar, and Drive integration hooks
- a local development workflow suitable for demos and evaluation

## Tech Stack

- Frontend: Next.js, React, Tailwind CSS, TypeScript
- Backend: FastAPI, SQLAlchemy Async, Alembic, Pydantic
- Database: SQLite
- PDF parsing: PyMuPDF
- LLM provider: OpenAI
- Cloud integrations: Google OAuth 2.0, Google Calendar API, Google Drive API
- Python environment: `uv` with Python 3.11
- Node environment: `nvm` with Node `v24.15.0`

## Repository Structure

```text
learn_pilot/
├── backend/                # FastAPI backend, database models, migrations, tests
├── frontend/               # Next.js frontend MVP
├── docs/                   # Supporting project documentation
├── infra/                  # Infrastructure helpers
├── SoftwareEngineeringPlan.md
└── Project 2026.pdf
```

## Before You Start

You will need:

- Python 3.11
- `uv`
- Node.js `v24.15.0`
- npm `11+`
- an OpenAI account with API access
- a Google Cloud project with Calendar and Drive APIs enabled

## Backend Configuration

First, create your backend environment file:

```bash
cd backend
cp .env.example .env
```

### Required Backend Variables

```env
APP_NAME=LearnPilot
APP_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./data/learnpilot.db

JWT_SECRET_KEY=your-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
APP_ENCRYPTION_KEY=your-fernet-key

OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini

UPLOAD_DIR=data/uploads

GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/credentials/google/callback
GOOGLE_OAUTH_STATE_SECRET=your-random-google-state-secret
GOOGLE_DRIVE_ROOT_FOLDER_NAME=LearnPilot
```

### Generate Local Security Secrets

Three backend values must be generated locally:

- `JWT_SECRET_KEY`
- `APP_ENCRYPTION_KEY`
- `GOOGLE_OAUTH_STATE_SECRET`

You can generate them with:

```bash
cd backend
uv run python - <<'PY'
from cryptography.fernet import Fernet
import secrets

print("APP_ENCRYPTION_KEY=", Fernet.generate_key().decode(), sep="")
print("JWT_SECRET_KEY=", secrets.token_urlsafe(32), sep="")
print("GOOGLE_OAUTH_STATE_SECRET=", secrets.token_urlsafe(32), sep="")
PY
```

## Frontend Configuration

The frontend uses a same-origin proxy route, so the browser only talks to the Next.js app. The frontend then forwards API traffic to the FastAPI backend.

Create a frontend environment file if you want a local override:

```bash
cd frontend
cp .env.example .env.local
```

### Required Frontend Variable

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

This should point to the running FastAPI backend origin. The frontend proxy will automatically forward requests to the backend API namespace, so `http://localhost:8000` is the recommended value. `http://localhost:8000/api` is also accepted for compatibility.

## External Service Setup

### OpenAI

LearnPilot uses OpenAI as the default LLM provider.

What you need to do:

1. Sign in to the OpenAI Platform.
2. Create a secret API key.
3. Keep that key safe.
4. Start LearnPilot and save the key through the app settings or backend API.

Important note:

- The OpenAI API key is **not** stored in `backend/.env`.
- It is stored per user through the backend endpoint `POST /api/credentials/llm`.

Backend defaults for OpenAI:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

Useful references:

- OpenAI API key help: https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key
- OpenAI API authentication: https://platform.openai.com/docs/api-reference/introduction/installation
- `gpt-4.1-mini` model reference: https://platform.openai.com/docs/models/gpt-4.1-mini

### Google OAuth, Calendar, and Drive

LearnPilot uses Google for:

- OAuth sign-in authorization flow
- Google Calendar event creation
- Google Drive PDF archiving

The backend currently requests these scopes:

- `https://www.googleapis.com/auth/calendar.events`
- `https://www.googleapis.com/auth/drive.file`
- `openid`
- `https://www.googleapis.com/auth/userinfo.email`

Setup steps:

1. Open Google Cloud Console.
2. Create a new project, or select an existing one.
3. Enable:
   - Google Calendar API
   - Google Drive API
4. Configure the OAuth consent screen.
   - For local development, `External` is usually the easiest choice.
   - Add your Google account to the test users list if the app is still in testing mode.
   - In Google Auth Platform > Audience, either publish the app or explicitly add your Google account as a test user before trying to connect LearnPilot.
5. Create OAuth credentials.
   - Choose **Web application**.
   - Add this exact redirect URI:
     `http://localhost:8000/api/credentials/google/callback`
6. Copy the generated:
   - Client ID
   - Client Secret
7. Paste them into `backend/.env`.

Important note:

- `GOOGLE_OAUTH_REDIRECT_URI` in your `.env` must exactly match the redirect URI configured in Google Cloud Console.
- If the app is not published yet, only users listed in Google Auth Platform > Audience > Test users will be able to complete the OAuth flow.

Useful references:

- OAuth consent setup: https://developers.google.com/workspace/guides/configure-oauth-consent
- Create Google credentials: https://developers.google.com/workspace/guides/create-credentials
- Web server OAuth flow: https://developers.google.com/identity/protocols/oauth2/web-server
- Drive auth scopes: https://developers.google.com/workspace/drive/api/guides/api-specific-auth

## How to Run the Backend

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Run database migrations

```bash
cd backend
uv run alembic upgrade head
```

### 3. Start the backend server

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running, you can open:

- Health check: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## How to Run the Frontend

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Start the frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at:

- `http://localhost:3000`

## Recommended Local Development Flow

If you want the full experience, I recommend this order:

1. Configure `backend/.env`
2. Configure `frontend/.env.local`
3. Start the backend
4. Start the frontend
5. Open `http://localhost:3000`
6. Create an account
7. Save your OpenAI API key in **Settings**
8. Connect your Google account in **Settings**
9. Upload a study PDF from the dashboard
10. Run analysis and review the generated note and candidate events

## Frontend Overview

The frontend MVP currently includes:

- a landing page introducing LearnPilot
- login and registration pages
- an authenticated dashboard
- document upload and recent-document browsing
- document detail pages with:
  - extracted text preview
  - analysis controls
  - generated note editing
  - candidate event review
  - Google Drive archive status
- a settings page for:
  - profile updates
  - OpenAI key storage
  - Google connection status

The frontend uses localStorage for the access token and validates it on app startup by calling `/api/auth/me`.

## Testing and Verification

### Backend checks

```bash
cd backend
uv run ruff check app tests
uv run pytest
```

### Frontend checks

```bash
cd frontend
npm run typecheck
npm run lint
npm run build
```

## Typical User Journey

This is the path I expect most users to follow:

1. Create an account
2. Sign in
3. Configure an OpenAI API key
4. Connect Google Calendar and Drive
5. Upload a text-based academic PDF
6. Run analysis
7. Review notes and extracted candidate events
8. Approve selected events for Google Calendar
9. Archive the original PDF to Google Drive if desired

## Notes for Evaluators and Teammates

- The current backend uses SQLite for local development and demonstration.
- The current analysis flow is synchronous, which makes the system easier to test and demo.
- The Google OAuth callback remains backend-owned; the frontend handles Google connection by opening the authorization flow and polling credential status afterward.
- The repository contains working MVP code, but it is still a course project prototype rather than a production deployment.

## Security Reminder

- Do not commit `backend/.env` or `frontend/.env.local`.
- If any secret or API key has been exposed in screenshots, chat messages, or a public repository, rotate it immediately.

## Project Intention

I built LearnPilot to show that a personal assistant does not need to be a vague “AI agent” concept. It can be implemented as a practical, modular service platform with clear APIs, clear workflows, and a focused user problem: helping students turn academic documents into action.
