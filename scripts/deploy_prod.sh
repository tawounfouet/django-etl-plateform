#!/bin/bash
cd /workspaces/django-etl-plateform
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=etl_platform.settings.prod

# Vérifications pré-déploiement
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput

# Lancer avec Gunicorn
gunicorn etl_platform.wsgi:application --bind 0.0.0.0:8000 --workers 3
