#!/bin/sh
set -e

echo "Waiting for database..."

python - <<'PY'
import os
import re
import time

import psycopg2

database_url = os.environ.get('DATABASE_URL', '')
match = re.match(r'postgresql://(\w+):(\w+)@([\w.]+):(\d+)/(\w+)', database_url)
if not match:
    raise SystemExit('Invalid or missing DATABASE_URL')

connection_params = {
    'dbname': match.group(5),
    'user': match.group(1),
    'password': match.group(2),
    'host': match.group(3),
    'port': match.group(4),
}

for attempt in range(60):
    try:
        connection = psycopg2.connect(**connection_params)
        connection.close()
        break
    except Exception:
        if attempt == 59:
            raise
        time.sleep(2)
PY

python manage.py migrate --noinput

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000