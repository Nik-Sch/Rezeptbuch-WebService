#!/bin/sh
cd /opt/webservice/rezeptbuch/
mv service.log service.log.bak
. venv/bin/activate
python app.py 2>&1 | tee service.log
deactivate
