# Notes AI API (FastAPI + Postgres + Redis + RQ)

Small REST API that authenticates users with JWT, stores notes in Postgres, and asynchronously “summarizes” them with an RQ worker (Redis queue) and llm model(sshleifer-distilbart-cnn-12-6). Ships with Docker Compose, Swagger UI, Alembic migrations, and basic tests.

---
# To start the app from 0

Powershell
```powershell
.\bootstrap-compose.ps1
```
Linux
```bash
chmod +x bootstrap-compose.sh
```
## Tech Stack
- **Language:** Python 3.10  
- **Framework:** FastAPI (Uvicorn)
- **DB & ORM:** PostgreSQL + SQLAlchemy 2.0
- **Migrations:** Alembic
- **Queue:** Redis + RQ
- **Validation:** Pydantic v2
- **Auth:** JWT (python-jose), bcrypt (passlib)
- **Retries:** tenacity
- **Containers:** Docker & Docker Compose
- **Tests:** pytest, httpx, fakeredis

---

## TL;DR – Quick Start (Docker Compose)

### 0) Prerequisites
- Docker Desktop + Git

### 1) Env

**`.env` (safe for local/dev)**
```env
ENV=local
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/appdb
REDIS_URL=redis://redis:6379/0
RQ_QUEUE_NAME=notes_summarize

JWT_SECRET=dev-only-not-for-prod
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
TOKEN_AUDIENCE=notes-api
TOKEN_ISSUER=notes-api

# seed (first boot; idempotent)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=Admin123!
```

### 2) Start the stack
```bash
docker compose up -d --build
```
- API waits for Postgres, runs **Alembic migrations**, **seeds** 1 admin  then starts
- Worker starts and listens on the `notes_summarize` queue

### 3) Use Swagger & test
- Open: **http://localhost:8000/docs**
- Login with seeded admin: `admin@example.com` / `Admin123!`
- Create a note (`POST /api/v1/notes`), then fetch (`GET /api/v1/notes/{id}`)

### 4) Logs (handy)
```bash
docker compose logs -f api
docker compose logs -f worker
```

---

## What the App Does
Example note:

Morning unfurled like a slow ribbon across the rooftops as kettles hissed, buses sighed, and sparrows rehearsed brave little arias on sagging wires. Keys clinked by doorways, screens woke, and bread steamed under butter’s bright rush. In the pause before meetings and messages, someone watered a fern, another tied a shoe, and a child asked why clouds move. Answers came gently: because wind wanders, because days begin, because we do, too. The kettle clicked; nearby, a bike bell chimed twice. Soft.

### Authentication & Tenancy
- Email/password signup & login (bcrypt hashing)
- JWT access tokens with:
  - **JTI blacklist** stored in Redis (logout invalidates current token)
  - **Token versioning** (global invalidate by bumping version)
- Roles: `ADMIN`, `AGENT`
  - **Agents**: only their own notes
  - **Admins**: can access any note; can list users; can view grouped reports

### Models
- **users**: `id, email, password_hash, role, token_version, created_at, updated_at`
- **notes**: `id, user_id, raw_text, summary, status(queued|processing|done|failed), idempotency_key, created_at, updated_at`
- Managed with **Alembic** migrations

### Async Summarization
- `POST /api/v1/notes` creates a note with `status="queued"` and **enqueues** an RQ job
- Worker updates `status` → `processing` → `done/failed`, writes `summary`
- **Retries** with exponential backoff (tenacity)
- **Idempotency** via optional `Idempotency-Key` header (per user); safe re-tries

### Minimal Endpoint Map
- **Auth**
  - `POST /api/v1/auth/signup` – create AGENT by default  
  - `POST /api/v1/auth/login` – returns `access_token`  
  - `GET  /api/v1/auth/me` – current user info (Bearer)  
  - `POST /api/v1/auth/logout` – blacklist current token
- **Users (ADMIN)**
  - `GET  /api/v1/users` – list users (no notes)
- **Notes**
  - `POST /api/v1/notes` – create & enqueue (Idempotency-Key optional)
  - `GET  /api/v1/notes` – **current user’s notes only** (even for admins); supports `status`, `limit`, `offset`
  - `GET  /api/v1/notes/{note_id}` – get one note (tenancy enforced)
  - `GET  /api/v1/notes/all` (ADMIN) – all notes; supports `status`, `limit`, `offset`
  - `GET  /api/v1/notes/grouped-by-user` (ADMIN) – users + their notes; optional `status` filter
- **Health**
  - `GET /health` – `{ "status": "ok" }`

---

## Testing
```bash
# run unit tests (SQLite + fakeredis; no external services needed)
pytest -q
```
Tests use:
- **SQLite in-memory** with SQLAlchemy `StaticPool` for FastAPI TestClient
- **fakeredis** to emulate Redis (so RQ enqueue doesn’t require a real Redis)
- **httpx/Starlette TestClient** for HTTP calls

---

## Migrations
- **Autogenerate** when models change:
  ```bash
  alembic revision -m "your message" --autogenerate
  ```
- **Apply**:
  ```bash
  alembic upgrade head
  ```
- Docker Compose runs migrations automatically on start via `start.sh` / `start_worker.sh`.

---

## Security Notes
- Passwords: **bcrypt** via passlib
- JWT: **HS256**, **JTI blacklist** in Redis, **token_version** for global invalidation
- SQL injection: prevented via SQLAlchemy ORM/parameters (no raw SQL in endpoints)
- CORS: `*` in dev (tighten for prod)
- Idempotency: `Idempotency-Key` header on note creation
- Background jobs: **retries** with exponential backoff, no user tokens stored in jobs
