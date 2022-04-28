#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py makemigrations
python manage.py migrate

gunicorn digitalshopapp.wsgi:application --bind 0.0.0.0:$PORT