#!/usr/bin/env bash
set -euo pipefail

# Simple helper to build and start the stack
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

if [ ! -f .env ]; then
  echo "Creating default .env from template values..."
  cat > .env <<'EOF'
APP_ENV=development
BACKEND_PORT=8000
FRONTEND_PORT=5173
VITE_API_URL=http://localhost:8000
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=intelliscalesim
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/intelliscalesim
CORS_ORIGINS=*
EOF
fi

docker compose up --build
