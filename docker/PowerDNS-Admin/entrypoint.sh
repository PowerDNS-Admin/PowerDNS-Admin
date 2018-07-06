#!/bin/bash

set -o nounset
set -o errexit
set -o pipefail


# == Vars
#
DB_MIGRATION_DIR='/powerdns-admin/migrations'


# Wait for us to be able to connect to MySQL before proceeding
echo "===> Waiting for $PDA_DB_HOST MySQL service"
until nc -zv \
  $PDA_DB_HOST \
  3306;
do
  echo "MySQL ($PDA_DB_HOST) is unavailable - sleeping"
  sleep 1
done


echo "===> DB management"
# Go in Workdir
cd /powerdns-admin

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


echo "===> Assets management"
echo "---> Running Yarn"
chown -R www-data:www-data /powerdns-admin/app/static
chown -R www-data:www-data /powerdns-admin/node_modules
su -s /bin/bash -c 'yarn install --pure-lockfile' www-data

echo "---> Running Flask assets"
chown -R www-data:www-data /powerdns-admin/logs
su -s /bin/bash -c 'flask assets build' www-data


echo "===> Start supervisor"
/usr/bin/supervisord -c /etc/supervisord.conf
