#!/bin/sh
test -f ./filmaster.cfg && . ./filmaster.cfg
test -f "$VIRTUAL_ENV/bin/activate" && . "$VIRTUAL_ENV/bin/activate"
cd film20
PORT=${FCGIPORT:-9090}
MINSPARE=${MINSPARE:-4}
MAXSPARE=${MAXSPARE:-20}

echo $PORT

python manage.py runfcgi method=prefork host=127.0.0.1 port=$PORT pidfile=../filmaster_fcgi.pid minspare=$MINSPARE maxspare=$MAXSPARE daemonize=false
