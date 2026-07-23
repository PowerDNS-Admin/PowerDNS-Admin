#!/bin/sh

set -eu

rm -f /tmp/browser-test-ready

flask db upgrade
PYTHONPATH=/app python /opt/scenario/seed-browser-tests.py

flask run --host=0.0.0.0 --port=80 &
server_pid=$!

cleanup() {
    kill "${server_pid}" 2>/dev/null || true
    wait "${server_pid}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

attempt=0
until curl --fail --silent http://localhost/login >/dev/null; do
    attempt=$((attempt + 1))
    if [ "${attempt}" -ge 30 ]; then
        echo "Configured PowerDNS-Admin server did not start" >&2
        exit 1
    fi
    sleep 1
done

# Run the existing Python cases only after the real application deployment is
# migrated, seeded, serving HTTP, and verified against this profile's PDNS.
pytest -W ignore::DeprecationWarning --capture=no -vv

# The browser service cannot start until the deployment tests above pass.
touch /tmp/browser-test-ready
wait "${server_pid}"
