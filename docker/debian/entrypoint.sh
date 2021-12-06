#!/bin/bash

set -eo pipefail

GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_LOGLEVEL="${GUNICORN_LOGLEVEL:-info}"
BIND_ADDRESS="${BIND_ADDRESS:-0.0.0.0:80}"
GUNICORN_ARGS="-t ${GUNICORN_TIMEOUT} --workers ${GUNICORN_WORKERS} --log-level ${GUNICORN_LOGLEVEL}  --bind ${BIND_ADDRESS}"

cd /app

/bin/sh -c "flask db upgrade"

if [ "$1" = "gunicorn" ]; then
    exec "$@" $GUNICORN_ARGS
else
    exec "$@"
fi
