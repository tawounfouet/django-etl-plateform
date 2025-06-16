#!/bin/bash
cd /workspaces/django-etl-plateform
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=etl_platform.settings.dev
python manage.py runserver 0.0.0.0:8000
