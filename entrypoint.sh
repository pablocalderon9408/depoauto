#!/usr/bin/env sh
set -eu

: "${PORT:=8000}"

: "${RUN_MIGRATIONS_ON_START:=true}"
: "${RUN_COLLECTSTATIC_ON_START:=true}"
: "${USE_DEV_SERVER:=0}"

if [ "$RUN_MIGRATIONS_ON_START" = "true" ] || [ "$RUN_MIGRATIONS_ON_START" = "1" ]; then
  python manage.py migrate --noinput
fi

if [ "$RUN_COLLECTSTATIC_ON_START" = "true" ] || [ "$RUN_COLLECTSTATIC_ON_START" = "1" ]; then
  python manage.py collectstatic --noinput
fi

# Auto-creación de superusuario (opcional)
if [ "${AUTO_CREATE_SUPERUSER:-false}" = "true" ]; then
  if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "Auto-creando superusuario..."
    python manage.py createsuperuser --noinput || true
  else
    echo "AUTO_CREATE_SUPERUSER=true pero faltan variables: DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD"
  fi
fi

if [ "$USE_DEV_SERVER" = "true" ] || [ "$USE_DEV_SERVER" = "1" ]; then
  exec python manage.py runserver 0.0.0.0:${PORT}
fi

exec gunicorn depoauto.wsgi:application \
  --bind 0.0.0.0:${PORT} \
  --workers 3 \
  --timeout 120 \
  --access-logfile '-' --error-logfile '-'

