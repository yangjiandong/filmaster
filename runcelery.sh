#!/bin/sh
test -f ./filmaster.cfg && . ./filmaster.cfg
test -f "$VIRTUAL_ENV/bin/activate" && . "$VIRTUAL_ENV/bin/activate"

cd film20
python manage.py celeryd_detach --pidfile ../filmaster_celery.pid
