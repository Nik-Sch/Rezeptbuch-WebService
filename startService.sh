#!/bin/sh
cd /opt/webservice/rezeptbuch/
./app.py 2>&1 | tee service.log
