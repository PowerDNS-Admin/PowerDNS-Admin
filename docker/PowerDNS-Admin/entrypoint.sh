#!/bin/sh

cd /powerdns-admin

if [ ! -d "/powerdns-admin/migrations" ]; then
    flask db init --directory /powerdns-admin/migrations
    flask db migrate -m "Init DB" --directory /powerdns-admin/migrations
    flask db upgrade --directory /powerdns-admin/migrations
    ./init_data.py

else
    /usr/local/bin/flask db migrate -m "Upgrade BD Schema" --directory /powerdns-admin/migrations
    /usr/local/bin/flask db upgrade --directory /powerdns-admin/migrations
fi

yarn install --pure-lockfile
flask assets build

/usr/bin/supervisord -c /etc/supervisord.conf
