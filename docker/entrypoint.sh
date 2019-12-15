#!/bin/sh
set -euo pipefail
cd /app

GUNICORN_TIMEOUT="${GUINCORN_TIMEOUT:-120}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_LOGLEVEL="${GUNICORN_LOGLEVEL:-info}"
BIND_ADDRESS="${BIND_ADDRESS:-0.0.0.0:80}"

cat ./powerdnsadmin/default_config.py ./configs/docker_config.py > ./powerdnsadmin/docker_config.py

GUNICORN_ARGS="-t ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKERS} --bind ${BIND_ADDRESS} --log-level ${GUNICORN_LOGLEVEL}"
if [ "$1" == gunicorn ]; then
    flask db upgrade
    exec "$@" $GUNICORN_ARGS

else
    exec "$@"
fi
