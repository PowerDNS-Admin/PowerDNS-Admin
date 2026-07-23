#!/bin/sh

set -eu

cd /app

GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_LOGLEVEL="${GUNICORN_LOGLEVEL:-info}"
BIND_ADDRESS="${BIND_ADDRESS:-0.0.0.0:80}"

if [ "${1:-}" = "gunicorn" ]; then
    flask db upgrade
    exec "$@" \
        --timeout "${GUNICORN_TIMEOUT}" \
        --workers "${GUNICORN_WORKERS}" \
        --bind "${BIND_ADDRESS}" \
        --log-level "${GUNICORN_LOGLEVEL}"
fi

exec "$@"
