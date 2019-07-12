#!/bin/bash
set -Eeuo pipefail
cd /opt/powerdns-admin

if [ ! -f ./config.py ]; then
    cat ./config_template.py ./docker/Production/config_docker.py > ./config.py
fi

if [ "$1" == gunicorn ]; then
    flask db upgrade
fi

exec "$@"
