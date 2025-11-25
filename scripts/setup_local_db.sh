#!/usr/bin/env bash
set -euo pipefail
# Initialize a local PostgreSQL database for IntelliScaleSim.
# Prerequisites: postgres server installed and running (sudo apt install postgresql postgresql-contrib)
# Usage: ./scripts/setup_local_db.sh

DB_NAME=${DB_NAME:-intelliscalesim}
DB_USER=${DB_USER:-postgres}
DB_PASS=${DB_PASS:-postgres}
DB_PORT=${DB_PORT:-5432}

echo "[info] Ensuring PostgreSQL is reachable on localhost:$DB_PORT ..."
if ! pg_isready -q -h localhost -p "$DB_PORT"; then
  echo "[warn] Postgres not ready on localhost:$DB_PORT. If service is stopped, try: sudo systemctl start postgresql"
fi

echo "[info] Checking if database '$DB_NAME' exists..."
set +e
psql -h localhost -U "$DB_USER" -p "$DB_PORT" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null | grep -q 1
PSQL_OK=$?
set -e

if [ $PSQL_OK -ne 0 ]; then
  echo "[info] Creating database using OS 'postgres' user to bypass peer auth..."
  if command -v sudo >/dev/null 2>&1; then
    sudo -u postgres createdb -p "$DB_PORT" "$DB_NAME" 2>/dev/null || true
    echo "[info] Setting password for role '$DB_USER' (may prompt for sudo)..."
    sudo -u postgres psql -p "$DB_PORT" -c "ALTER USER \"$DB_USER\" WITH PASSWORD '$DB_PASS';" >/dev/null || true
  else
    echo "[error] 'sudo' not available. Run the following manually as the 'postgres' OS user:"
    echo "       createdb -p $DB_PORT $DB_NAME"
    echo "       psql -p $DB_PORT -c \"ALTER USER \"$DB_USER\" WITH PASSWORD '$DB_PASS';\""
    exit 1
  fi
else
  echo "[skip] Database already exists."
fi

echo "[info] Verifying connection with password over TCP..."
export PGPASSWORD="$DB_PASS"
psql -h localhost -U "$DB_USER" -p "$DB_PORT" -d "$DB_NAME" -c "SELECT 1;" >/dev/null
unset PGPASSWORD

echo "[done] Local Postgres ready. Set DATABASE_URL='postgresql+psycopg2://$DB_USER:$DB_PASS@localhost:$DB_PORT/$DB_NAME'"
