#!/bin/sh

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

cd /powerdns-admin
./create_db.py
yarn install --pure-lockfile
FLASK_APP=app/__init__.py flask assets build

/usr/bin/supervisord -c /etc/supervisord.conf
