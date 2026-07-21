#!/bin/sh

set -e

case "${POWERDNS_ADMIN_MODE:-dev}" in
  dev)
    exec /opt/wait-for-pdns.sh /bin/sh -c \
      'flask db upgrade && exec flask run --host=0.0.0.0 --port=80 --debug'
    ;;
  test)
    exec /opt/wait-for-pdns.sh /opt/venv/bin/pytest \
      -W ignore::DeprecationWarning --capture=no -vv
    ;;
  *)
    >&2 echo "Unsupported POWERDNS_ADMIN_MODE: ${POWERDNS_ADMIN_MODE}. Expected dev or test."
    exit 2
    ;;
esac
