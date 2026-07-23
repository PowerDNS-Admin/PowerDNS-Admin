#!/bin/sh

set -e

exec /opt/wait-for-pdns.sh /opt/venv/bin/pytest \
  -W ignore::DeprecationWarning --capture=no -vv
