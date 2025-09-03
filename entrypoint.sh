#!/usr/bin/env sh
set -eu

: "${PORT:=8000}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn depoauto.wsgi:application \
  --bind 0.0.0.0:${PORT} \
  --workers 3 \
  --timeout 120 \
  --access-logfile '-' --error-logfile '-'

