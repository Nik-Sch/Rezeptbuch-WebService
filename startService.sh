#!/bin/sh
cd /opt/webservice/rezeptbuch/
mv service.log service.log.bak
. venv/bin/activate
gunicorn --workers=4 -b 0.0.0.0:5425 --access-logfile - app:app |& tee service.log
deactivate
