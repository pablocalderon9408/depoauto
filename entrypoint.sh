#!/usr/bin/env sh
set -eu

: "${PORT:=8000}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Auto-creación de superusuario (opcional)
if [ "${AUTO_CREATE_SUPERUSER:-false}" = "true" ]; then
  if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "Auto-creando superusuario..."
    python manage.py createsuperuser --noinput || true
  else
    echo "AUTO_CREATE_SUPERUSER=true pero faltan variables: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD"
  fi
fi

exec gunicorn depoauto.wsgi:application \
  --bind 0.0.0.0:${PORT} \
  --workers 3 \
  --timeout 120 \
  --access-logfile '-' --error-logfile '-'

