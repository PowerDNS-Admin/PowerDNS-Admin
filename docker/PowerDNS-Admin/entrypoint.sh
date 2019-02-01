#!/bin/sh

set -o errexit
set -o pipefail


# == Vars
#
DB_MIGRATION_DIR='/powerdns-admin/migrations'
if [ -z ${PDNS_PROTO} ];
 then PDNS_PROTO="http"
fi

if [ -z ${PDNS_PORT} ];
 then PDNS_PORT=8081
fi

# Wait for us to be able to connect to MySQL before proceeding
echo "===> Waiting for $PDA_DB_HOST MySQL service"
until nc -zv $PDA_DB_HOST $PDA_DB_PORT;
do
  echo "MySQL ($PDA_DB_HOST) is unavailable - sleeping"
  sleep 1
done

# Go in Workdir
cd /powerdns-admin

echo "===> Set configuration file from environment variable"
[ -n "$SECRET_KEY" ] && sed -i "s/^\(SECRET_KEY\)/\1 = '$SECRET_KEY'/" config.py
[ -n "$PDNS_PORT" ] && sed -i "s/^\(PORT\)/\1 = $PDNS_PORT/" config.py
[ -n "$BIND_ADDRESS" ] && sed -i "s/^\(BIND_ADDRESS\)/\1 = '$BIND_ADDRESS'/" config.py
[ -n "$PDA_DB_USER" ] && sed -i "s/^\(SQLA_DB_USER\)/\1 = '$PDA_DB_USER'/" config.py
[ -n "$PDA_DB_PASSWORD" ] && sed -i "s/^\(SQLA_DB_PASSWORD\)/\1 = '$PDA_DB_PASSWORD'/" config.py
[ -n "$PDA_DB_HOST" ] && sed -i "s/^\(SQLA_DB_HOST\)/\1 = '$PDA_DB_HOST'/" config.py
[ -n "$PDA_DB_PORT" ] && sed -i "s/^\(SQLA_DB_PORT\)/\1 = $PDA_DB_PORT/" config.py
[ -n "$PDA_DB_NAME" ] && sed -i "s/^\(SQLA_DB_NAME\)/\1 = '$PDA_DB_NAME'/" config.py
[ -n "$LDAP_TYPE" ] && sed -i "s/^\(LDAP_TYPE\)/\1 = '$LDAP_TYPE'/" config.py
[ -n "$LDAP_URI" ] && sed -i "s/^\(LDAP_URI\)/\1 = '$LDAP_URI'/" config.py
[ -n "$LDAP_USERNAME" ] && sed -i "s/^\(LDAP_USERNAME\)/\1 = '$LDAP_USERNAME'/" config.py
[ -n "$LDAP_PASSWORD" ] && sed -i "s/^\(LDAP_PASSWORD\)/\1 = '$LDAP_PASSWORD'/" config.py
[ -n "$LDAP_SEARCH_BASE" ] && sed -i "s/^\(LDAP_SEARCH_BASE\)/\1 = '$LDAP_SEARCH_BASE'/" config.py
[ -n "$LDAP_USERNAMEFIELD" ] && sed -i "s/^\(LDAP_USERNAMEFIELD\)/\1 = '$LDAP_USERNAMEFIELD'/" config.py
[ -n "$LDAP_FILTER" ] && sed -i "s/^\(LDAP_FILTER\)/\1 = '$LDAP_FILTER'/" config.py
[ -n "$PDNS_STATS_URL" ] && sed -i "s/^\(PDNS_STATS_URL\)/\1 = '$PDNS_STATS_URL'/" config.py
[ -n "$PDNS_API_KEY" ] && sed -i "s/^\(PDNS_API_KEY\)/\1 = '$PDNS_API_KEY'/" config.py
[ -n "$BIND_ADDRESS" ] && sed -i "s/^\(SECRET_KEY\)/\1 = '$BIND_ADDRESS'/" config.py
[ -n "$BIND_ADDRESS" ] && sed -i "s/^\(SECRET_KEY\)/\1 = '$BIND_ADDRESS'/" config.py

echo "===> DB management"
if [ ! -d "${DB_MIGRATION_DIR}" ]; then
  echo "---> Running DB Init"
  flask db init --directory ${DB_MIGRATION_DIR}
  flask db migrate -m "Init DB" --directory ${DB_MIGRATION_DIR}
  flask db upgrade --directory ${DB_MIGRATION_DIR}
  ./init_data.py

else
  echo "---> Running DB Migration"
  set +e
  flask db migrate -m "Upgrade BD Schema" --directory ${DB_MIGRATION_DIR}
  flask db upgrade --directory ${DB_MIGRATION_DIR}
  set -e
fi

echo "===> Update PDNS API connection info"
# initial setting if not available in the DB
mysql -h${PDA_DB_HOST} -u${PDA_DB_USER} -p${PDA_DB_PASSWORD} -P${PDA_DB_PORT} ${PDA_DB_NAME} -e "INSERT INTO setting (name, value) SELECT * FROM (SELECT 'pdns_api_url', '${PDNS_PROTO}://${PDNS_HOST}:${PDNS_PORT}') AS tmp WHERE NOT EXISTS (SELECT name FROM setting WHERE name = 'pdns_api_url') LIMIT 1;"
mysql -h${PDA_DB_HOST} -u${PDA_DB_USER} -p${PDA_DB_PASSWORD} -P${PDA_DB_PORT} ${PDA_DB_NAME} -e "INSERT INTO setting (name, value) SELECT * FROM (SELECT 'pdns_api_key', '${PDNS_API_KEY}') AS tmp WHERE NOT EXISTS (SELECT name FROM setting WHERE name = 'pdns_api_key') LIMIT 1;"

# update pdns api setting if .env is changed.
mysql -h${PDA_DB_HOST} -u${PDA_DB_USER} -p${PDA_DB_PASSWORD} -P${PDA_DB_PORT} ${PDA_DB_NAME} -e "UPDATE setting SET value='${PDNS_PROTO}://${PDNS_HOST}:${PDNS_PORT}' WHERE name='pdns_api_url';"
mysql -h${PDA_DB_HOST} -u${PDA_DB_USER} -p${PDA_DB_PASSWORD} -P${PDA_DB_PORT} ${PDA_DB_NAME} -e "UPDATE setting SET value='${PDNS_API_KEY}' WHERE name='pdns_api_key';"

echo "===> Assets management"
echo "---> Running Yarn"
chown -R www-data:www-data /powerdns-admin/app/static
chown -R www-data:www-data /powerdns-admin/node_modules
su -s /bin/bash -c 'yarn install --pure-lockfile' www-data

echo "---> Running Flask assets"
chown -R www-data:www-data /powerdns-admin/logs
su -s /bin/bash -c 'flask assets build' www-data

echo "===> Start powerDNS-Admin"
su-exec www-data /usr/local/bin/gunicorn -t 120 --workers 4 --bind '0.0.0.0:9191' --log-level info app:app