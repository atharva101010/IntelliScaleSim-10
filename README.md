# IntelliScaleSim

IntelliScaleSim (Intelligent Scaling Simulator) is a cloud simulation platform for education and research. This repo currently contains a scaffold with a FastAPI backend and a React (TypeScript + Vite + TailwindCSS) frontend, wired with Docker Compose and PostgreSQL. No business logic yet — just structure.

## Structure

- `backend/` — FastAPI skeleton, requirements, Dockerfile
- `frontend/` — React + Vite + Tailwind scaffold, Dockerfile
- `infrastructure/` — docker-compose.yml, .env, nginx config

## Quick start (dev)

Prereqs: Docker + Docker Compose.

```
cd infrastructure
cp .env .env.local || true
# Update .env as needed, then:
docker compose up --build
```

Open:
- Backend API: http://localhost:8000/
- Health: http://localhost:8000/healthz
- Frontend: http://localhost:5173/

## Local (without Docker)

Backend:
```
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:
```
cd frontend
npm install
npm run dev
```

## Next steps

### Email (SMTP)

By default, emails are logged to the backend console (no real delivery). To send real emails, set SMTP variables in `infrastructure/.env` and restart Docker Compose:

Required:
- `SMTP_HOST`, `SMTP_PORT`
- `SMTP_USER`, `SMTP_PASSWORD`
- Either `SMTP_USE_TLS=true` (port 587) or `SMTP_USE_SSL=true` (port 465)
- `MAIL_FROM` e.g., `IntelliScaleSim <no-reply@yourdomain.com>`

Examples are provided at the bottom of `infrastructure/.env` for Gmail (App Password) and Mailtrap.

Restart:
```
cd infrastructure
docker compose down
docker compose up -d --build
```

Verify by registering a user or using Forgot Password; a real email should arrive.

### Roadmap

- Add Alembic migrations for DB schema
- Build dashboard and protected routes
- Optional: Nginx reverse proxy for prod
