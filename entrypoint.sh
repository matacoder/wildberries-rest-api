#!/bin/sh

sleep 2
python manage.py migrate
python manage.py createcachetable

if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser \
    --noinput \
    --username "$DJANGO_SUPERUSER_USERNAME" \
    --email $DJANGO_SUPERUSER_EMAIL
fi

python manage.py collectstatic --noinput
# python manage.py refresh &
gunicorn _settings.wsgi:application --bind 0.0.0.0:8000 --timeout 240

exec "$@"
