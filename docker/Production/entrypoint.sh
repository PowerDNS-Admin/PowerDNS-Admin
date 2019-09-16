#!/bin/bash
set -Eeuo pipefail
cd /opt/powerdns-admin

GUNICORN_TIMEOUT="${GUINCORN_TIMEOUT:-120}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_LOGLEVEL="${GUNICORN_LOGLEVEL:-info}"
BIND_ADDRESS="${BIND_ADDRESS:-0.0.0.0:80}"

if [ ! -f ./config.py ]; then
    cat ./config_template.py ./docker/Production/config_docker.py > ./config.py
fi

GUNICORN_ARGS="-t ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKERS} --bind ${BIND_ADDRESS} --log-level ${GUNICORN_LOGLEVEL}"
if [ "$1" == gunicorn ]; then
    flask db upgrade
    exec "$@" $GUNICORN_ARGS

else
    exec "$@"
fi
