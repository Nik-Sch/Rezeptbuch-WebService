#!/bin/sh
cd /opt/webservice/rezeptbuch/
mv service.log service.log.bak
./app.py 2>&1 | tee service.log
