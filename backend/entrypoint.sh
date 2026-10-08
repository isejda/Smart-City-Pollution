#!/bin/sh
set -e

echo "Waiting for Postgres at $POSTGRES_HOST:$POSTGRES_PORT..."
while ! python -c "
import socket, os, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect((os.environ['POSTGRES_HOST'], int(os.environ['POSTGRES_PORT'])))
except OSError:
    sys.exit(1)
"; do
  sleep 1
done
echo "Postgres is up."

python manage.py migrate --noinput
python manage.py seed_data
# seed_data regenerates synthetic readings for every node on every boot, so
# the real history + AI forecast are re-applied on top of it right after.
python manage.py import_real_history
python manage.py generate_forecast
python manage.py collectstatic --noinput

exec python manage.py runserver 0.0.0.0:8000
