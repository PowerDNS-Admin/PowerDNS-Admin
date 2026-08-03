#!/bin/sh

set -e

exec /opt/wait-for-pdns.sh /bin/sh -c \
  'flask db upgrade && exec flask run --host=0.0.0.0 --port=80 --debug'
