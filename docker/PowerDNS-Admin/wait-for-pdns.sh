#!/bin/sh

set -e

CMD="$1"
shift
CMD_ARGS="$@"

LOOPS=100
COUNTER=1
until curl -H "X-API-Key: ${PDNS_API_KEY}" "${PDNS_PROTO}://${PDNS_HOST}:${PDNS_PORT}/api/v1/servers"; do
  >&2 echo "PDNS is unavailable - sleeping"
  sleep 1
  if [ $LOOPS -eq $COUNTER ]
  then
    exit 134
  fi
  COUNTER=$(( $COUNTER + 1 ))
done

sleep 5

>&2 echo "PDNS is up - executing command"
exec $CMD $CMD_ARGS
