#!/bin/sh
set -e

mkdir -p /data/media

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Serve with several workers and threads so a single idle or slow client
# connection (browsers routinely open speculative connections) cannot starve
# the server. Values can be overridden at runtime via environment variables.
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
