#!/usr/bin/env sh
set -e

mkdir -p /app/var/static /app/var/media
echo "entrypoint: settings=${DJANGO_SETTINGS_MODULE:-unset} database_url=${DATABASE_URL:-unset}"

python - <<'PY'
import os
import time

import psycopg

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("entrypoint: DATABASE_URL is not set; skipping DB wait")
    raise SystemExit(0)

for attempt in range(30):
    try:
        psycopg.connect(database_url).close()
        raise SystemExit(0)
    except Exception:
        time.sleep(1)

raise SystemExit("Database is not ready after 30 attempts")
PY

if [ "${RUN_COLLECTSTATIC}" = "1" ]; then
  python manage.py collectstatic --noinput
fi

if [ "${RUN_MIGRATIONS}" = "1" ]; then
  python manage.py migrate --noinput
fi

exec "$@"
