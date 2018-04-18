#!/bin/sh
cd /powerdns-admin && ./create_db.py
/usr/bin/supervisord -c /etc/supervisord.conf
