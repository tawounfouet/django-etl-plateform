#!/bin/bash
cd /workspaces/django-etl-plateform
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=etl_platform.settings.stg
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
