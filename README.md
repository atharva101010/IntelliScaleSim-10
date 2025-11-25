# IntelliScaleSim

IntelliScaleSim (Intelligent Scaling Simulator) is a cloud simulation platform for education and research. This repo currently contains a scaffold with a FastAPI backend and a React (TypeScript + Vite + TailwindCSS) frontend backed by PostgreSQL. No business logic yet — just structure.

## Structure

- `backend/` — FastAPI app and Python dependencies
- `frontend/` — React + Vite + Tailwind app
- `scripts/` — Helper utilities (e.g., `setup_local_db.sh` for PostgreSQL)

## Quick start (local only)

### Backend (FastAPI)

Run these commands from the repo root:

```
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/intelliscalesim
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API health: http://localhost:8000/healthz

### Frontend (Vite + React)

In another terminal:

```
cd frontend
npm install
npm run dev
```

App URL: http://localhost:5173/

The Vite dev server proxies `/api/*` to http://localhost:8000 (see `frontend/vite.config.ts`).

## Database Configuration

Default `DATABASE_URL` in `backend/app/core/config.py` targets a local PostgreSQL instance:

```
postgresql+psycopg2://postgres:postgres@localhost:5432/intelliscalesim
```

Recommended setup:

```
sudo apt update && sudo apt install -y postgresql postgresql-contrib
./scripts/setup_local_db.sh
export DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/intelliscalesim
```

The helper script creates the database (if missing), sets the postgres user password, and verifies TCP access.

## Environment Variables (Local Mode)

Set in your shell or a `.env.local` file (frontend):
- `VITE_API_URL` (optional, defaults to http://localhost:8000 thanks to the proxy)
- `DATABASE_URL` (override if using a different Postgres instance)
- SMTP vars (only if sending real email)

## Next steps

### Email (SMTP)

By default, emails are logged to the backend console (no real delivery). To send real emails, export the SMTP environment variables before starting the backend (or place them in `backend/.env`). Required values:

- `SMTP_HOST`, `SMTP_PORT`
- `SMTP_USER`, `SMTP_PASSWORD`
- Either `SMTP_USE_TLS=true` (port 587) or `SMTP_USE_SSL=true` (port 465)
- `MAIL_FROM` (e.g., `IntelliScaleSim <no-reply@yourdomain.com>`)

Restart the backend after changing these settings and test by triggering a verification or password reset email.

### Roadmap

- Add Alembic migrations for DB schema
- Build dashboard and protected routes
- Optional: Nginx reverse proxy for prod
