#!/usr/bin/env sh

if [ -z ${PDNS_API_KEY+x} ]; then
    API_KEY=changeme
fi

if [ -z ${PDNS_PORT+x} ]; then
    WEB_PORT=8081
fi

# Import a clean schema for a new database. Isolated test scenarios request a
# reset on every container start so state cannot leak between runs; development
# retains its database on ordinary restarts.
if [ "${PDNS_RESET_DATABASE:-0}" = "1" ] || [ ! -e "/data/pdns.db" ]; then
    rm -f /data/pdns.db
    sqlite3 /data/pdns.db < /opt/pdns.sqlite.sql
    echo "Imported schema structure"
fi

chown -R pdns:pdns /data/

/usr/sbin/pdns_server \
    --launch=gsqlite3 --gsqlite3-database=/data/pdns.db \
    --gsqlite3-dnssec=${PDNS_BACKEND_DNSSEC:-yes} \
    --default-api-rectify=${PDNS_DEFAULT_API_RECTIFY:-yes} \
    --webserver=yes --webserver-address=0.0.0.0 --webserver-port=${PDNS_PORT} \
    --api=yes --api-key=$PDNS_API_KEY --webserver-allow-from=${PDNS_WEBSERVER_ALLOW_FROM}
