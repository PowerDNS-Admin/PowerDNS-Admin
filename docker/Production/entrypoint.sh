#!/bin/bash
set -Eeuo pipefail
cd /opt/powerdns-admin

DB_MIGRATION_DIR='./migrations'

if [ ! -f ./config.py ]; then
    cat ./config_template.py ./docker/Production/config_docker.py > ./config.py
fi

if [ "$1" == gunicorn ]; then
    if [ ! -d "${DB_MIGRATION_DIR}" ]; then
        flask db init --directory ${DB_MIGRATION_DIR}
        flask db migrate -m "Init DB" --directory ${DB_MIGRATION_DIR}
        flask db upgrade --directory ${DB_MIGRATION_DIR}
        ./init_data.py
    else
        flask db migrate -m "Upgrade DB Schema" --directory ${DB_MIGRATION_DIR}
        flask db upgrade --directory ${DB_MIGRATION_DIR}
    fi
fi

exec "$@"
