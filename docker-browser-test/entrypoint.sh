#!/bin/sh

set -e

exec /opt/wait-for-pdns.sh /opt/scenario/run-test-environment.sh
