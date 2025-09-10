#!/usr/bin/env bash
# exit on error
set -o errexit

python manage.py migrate --noinput
python manage.py collectstatic --noinput
