# IntelliScaleSim Infrastructure

This folder contains Docker Compose and Nginx configuration for local development.

- `docker-compose.yml` brings up Postgres, Backend (FastAPI), and Frontend (Vite + React).
- `.env` contains environment variables used by Compose services.
- `nginx/` has a simple reverse proxy config (optional for later use).

## Quick start

1. Copy `.env` to your own `.env.local` if you want to customize; Compose uses `.env` directly.
2. From this directory:

```
docker compose up --build
```

Services will be available at:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- (Optional) Nginx: If you decide to add an nginx service, map port 80 in compose.

