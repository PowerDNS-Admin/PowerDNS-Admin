#!/bin/sh
set -e

# How many seconds to wait after a connection attempt failure before trying again
FAIL_DELAY=3

# How many seconds to wait after a successful connection attempt before proceeding to the next step
SUCCESS_DELAY=3

# How many connection attempts should be made before halting execution
MAX_ATTEMPTS=10

API_URI="${PDNS_PROTO}://${PDNS_HOST}:${PDNS_PORT}/api/v1/servers"
API_AUTH_HEADER="X-API-Key: ${PDNS_API_KEY}"
CMD="$1"
shift
CMD_ARGS="$@"

until curl -H "${API_AUTH_HEADER}" "${API_URI}"; do
  >&2 echo "\nPowerDNS Authoritative server API not online yet. Waiting for ${FAIL_DELAY} seconds..."
  sleep $FAIL_DELAY
  if [ $MAX_ATTEMPTS -eq 10 ]
  then
    break
  fi
done

sleep $SUCCESS_DELAY

>&2 echo "PowerDNS Authoritative server API is online. Proceeding with next script execution..."
exec $CMD $CMD_ARGS
