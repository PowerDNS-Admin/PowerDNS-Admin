#!/bin/sh

if [ ! -d "/powerdns-admin/migrations" ]; then
    /usr/local/bin/flask db init --directory /powerdns-admin/migrations
    /usr/local/bin/flask db migrate -m "Init DB" --directory /powerdns-admin/migrations
    /usr/local/bin/flask db upgrade --directory /powerdns-admin/migrations
    cd /powerdns-admin && ./init_data.py

else
    /usr/local/bin/flask db migrate -m "Upgrade BD Schema" --directory /powerdns-admin/migrations
    /usr/local/bin/flask db upgrade --directory /powerdns-admin/migrations
fi

/usr/bin/supervisord -c /etc/supervisord.conf
