#!/bin/sh

set -e

LOOPS=10
until curl --fail --silent --show-error \
  -H "X-API-Key: ${PDNS_API_KEY}" \
  "${PDNS_PROTO}://${PDNS_HOST}:${PDNS_PORT}/api/v1/servers" >/dev/null; do
  >&2 echo "PDNS is unavailable - sleeping"
  LOOPS=$((LOOPS - 1))
  if [ "$LOOPS" -eq 0 ]; then
    >&2 echo "PDNS did not become available"
    exit 1
  fi
  sleep 1
done

>&2 echo "PDNS is up - executing command"
exec "$@"
