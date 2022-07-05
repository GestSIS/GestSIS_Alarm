#!/bin/sh

cd gestsis_alarm

python manage.py migrate
python manage.py loaddata sis

exec "$@"
