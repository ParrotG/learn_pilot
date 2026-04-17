# LearnPilot

LearnPilot is a course project implementation for **Topic 2: Personal Assistant-as-a-Service**. The system targets academic PDF workflows and provides a conversation-first study assistant built on a FastAPI backend and a Next.js frontend.

Current capabilities include:

- text extraction from uploaded PDF documents
- conversation-centric LLM interaction
- Markdown-rendered assistant responses
- session note creation and assistant-driven note revision
- approval-based Google Calendar event creation
- Pandoc-based session note export to `docx` and `pptx`
- approval-based Google Drive upload for exported artifacts
- optional Google Drive archiving for original PDF documents

## Current Implementation Scope

The current repository state covers the following major product flows:

- authenticated web application with registration, login, profile update, and per-user credential storage
- chat-first workspace with conversation history and persistent messages
- conversation-level PDF attachment and document-aware assistant responses
- session note generation and note revision through assistant tool calls
- approval/resume tool runtime for external side effects
- Google Calendar integration for approved date events
- Pandoc export pipeline for session notes
- Google Drive upload for exported artifacts and archived PDFs
- SQLite-based local persistence for development and evaluation

## Tech Stack

- Frontend: Next.js, React, Tailwind CSS, TypeScript
- Backend: FastAPI, SQLAlchemy Async, Alembic, Pydantic
- Database: SQLite
- PDF parsing: PyMuPDF
- LLM provider: OpenAI
- External integrations: Google OAuth 2.0, Google Calendar API, Google Drive API
- Python runtime: Python 3.11 with `uv`
- Node runtime: Node `v24.15.0`
- Document export: Pandoc
- Container runtime: Docker Compose

## Repository Structure

```text
learn_pilot/
├── backend/                     # FastAPI backend, migrations, tests, local data
├── frontend/                    # Next.js frontend
├── infra/
│   └── docker/                  # Dockerfiles, compose file, startup scripts
├── docs/                        # Supporting project documentation
├── SoftwareEngineeringPlan.md   # Active engineering plan
└── Project 2026.pdf             # Assignment specification
```

## Prerequisites

### Manual local startup

Required tools:

- Python 3.11
- `uv`
- Node.js `v24.15.0`
- npm `11+`
- Pandoc
- OpenAI API access
- Google Cloud project with Calendar API and Drive API enabled

### Docker startup

Required tools:

- Docker
- Docker Compose
- OpenAI API access
- Google Cloud project with Calendar API and Drive API enabled

Important:

- `backend/.env` must be configured before startup.
- `frontend/.env.local` must also be created before startup.
- This requirement applies to both manual startup and Docker startup.

## Environment Configuration

## Backend Environment File

Create the backend environment file:

```bash
cd backend
cp .env.example .env
```

Recommended baseline:

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
EXPORT_DIR=data/exports
PANDOC_BINARY=pandoc

GOOGLE_OAUTH_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/credentials/google/callback
GOOGLE_OAUTH_STATE_SECRET=your-random-google-state-secret
GOOGLE_DRIVE_ROOT_FOLDER_NAME=LearnPilot
```

Three secrets must be generated locally:

- `JWT_SECRET_KEY`
- `APP_ENCRYPTION_KEY`
- `GOOGLE_OAUTH_STATE_SECRET`

Suggested generation command:

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

## Frontend Environment File

Create the frontend environment file:

```bash
cd frontend
cp .env.example .env.local
```

Required variable:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Notes:

- For manual startup, `http://localhost:8000` is the recommended backend origin.
- For Docker startup, the compose file overrides this value internally to `http://backend:8000`.
- Keeping `frontend/.env.local` present remains recommended for a consistent local project setup.

## External Service Setup

## OpenAI

OpenAI is used as the default LLM provider.

Important implementation detail:

- The OpenAI API key is not stored in `backend/.env`.
- The key is stored per user through the application after sign-in.
- Configuration is completed through the Settings page or the backend credential endpoint.

Backend defaults:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4.1-mini
```

References:

- OpenAI API key help: https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key
- OpenAI API authentication: https://platform.openai.com/docs/api-reference/introduction/installation
- `gpt-4.1-mini` model reference: https://platform.openai.com/docs/models/gpt-4.1-mini

## Google OAuth, Calendar, and Drive

Google integration is used for:

- OAuth authorization
- Google Calendar event creation
- Google Drive document archive and export artifact upload

Currently requested scopes:

- `https://www.googleapis.com/auth/calendar.events`
- `https://www.googleapis.com/auth/drive.file`
- `openid`
- `https://www.googleapis.com/auth/userinfo.email`

Setup steps:

1. Open Google Cloud Console.
2. Create or select a project.
3. Enable:
   - Google Calendar API
   - Google Drive API
4. Configure the OAuth consent screen.
5. Create OAuth credentials for a web application.
6. Add the following redirect URI exactly:
   - `http://localhost:8000/api/credentials/google/callback`
7. Copy the generated client ID and client secret into `backend/.env`.

Important:

- `GOOGLE_OAUTH_REDIRECT_URI` must exactly match the Google Cloud configuration.
- If the OAuth app is still in testing mode, the Google account used for testing must be listed in the test users configuration.

References:

- OAuth consent setup: https://developers.google.com/workspace/guides/configure-oauth-consent
- Create Google credentials: https://developers.google.com/workspace/guides/create-credentials
- Web server OAuth flow: https://developers.google.com/identity/protocols/oauth2/web-server
- Drive auth scopes: https://developers.google.com/workspace/drive/api/guides/api-specific-auth

## Docker Startup

Container assets are provided under `infra/docker`.

Included files:

- `infra/docker/docker-compose.yml`
- `infra/docker/backend.Dockerfile`
- `infra/docker/frontend.Dockerfile`
- `infra/docker/backend-entrypoint.sh`
- `infra/docker/build.sh`
- `infra/docker/up.sh`
- `infra/docker/down.sh`
- `infra/docker/logs.sh`

Behavior:

- backend image includes Pandoc
- backend container automatically runs `alembic upgrade head` before service startup
- frontend container runs the production Next.js server
- backend data is persisted through the bind-mounted `backend/data` directory

### Docker startup steps

1. Configure `backend/.env`.
2. Configure `frontend/.env.local`.
3. Start services:

```bash
bash infra/docker/up.sh
```

4. View logs if needed:

```bash
bash infra/docker/logs.sh
```

5. Stop services:

```bash
bash infra/docker/down.sh
```

Optional image build command:

```bash
bash infra/docker/build.sh
```

Equivalent raw Docker Compose command:

```bash
docker compose -f infra/docker/docker-compose.yml up --build -d
```

Service endpoints after successful startup:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8000`
- backend health check: `http://localhost:8000/health`
- backend Swagger UI: `http://localhost:8000/docs`

## Manual Local Startup

## Backend startup

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Install Pandoc

Pandoc is required for note export to `docx` and `pptx`.

WSL/Linux installation:

```bash
sudo apt-get update
sudo apt-get install -y pandoc
pandoc --version
```

If Pandoc is installed outside the default `PATH`, set `PANDOC_BINARY` in `backend/.env`.

### 3. Run database migrations

```bash
cd backend
uv run alembic upgrade head
```

### 4. Start the backend service

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend startup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Start the frontend service

```bash
cd frontend
npm run dev
```

Service endpoints:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8000`

## Suggested Validation Flow

Recommended end-to-end validation sequence:

1. Create an account.
2. Sign in.
3. Configure the OpenAI API key in Settings.
4. Connect Google credentials in Settings.
5. Create a new chat.
6. Upload a PDF to the conversation.
7. Request a summary or a study note.
8. Request calendar event creation and approve the tool call.
9. Request note export to `docx` or `pptx` and approve the tool call.
10. Download the generated artifact.
11. Request Drive upload for the exported artifact and approve the tool call.

## Frontend Overview

The current frontend includes:

- public landing page
- login and registration pages
- chat-first authenticated workspace
- conversation history in the sidebar
- session note panel
- export artifact panel
- dashboard overview
- settings page for profile and credential configuration

Assistant responses and notes are rendered as Markdown.

## Backend Overview

The current backend includes:

- authentication and JWT session support
- encrypted per-user credential storage
- PDF upload and text extraction
- conversation, message, and run persistence
- session note persistence and revision tracking
- approval-based tool call runtime
- Google Calendar event creation
- Google Drive file upload flows
- Pandoc export artifact generation
- Alembic migration support

## Testing and Verification

## Backend checks

```bash
cd backend
uv run ruff check app tests
uv run pytest
```

## Frontend checks

```bash
cd frontend
npm run typecheck
npm run lint
npm run build
```

## Notes

- SQLite is used for local development and evaluation.
- Exported artifacts are stored under `backend/data/exports`.
- Uploaded PDFs are stored under `backend/data/uploads`.
- Docker startup installs Pandoc inside the backend image automatically.
- Manual startup requires Pandoc to be installed on the host system.
