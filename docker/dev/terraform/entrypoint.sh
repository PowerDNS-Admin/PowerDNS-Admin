#!/bin/sh

set -eu

: "${PDNS_SERVER_URL:?PDNS_SERVER_URL must contain the PowerDNS API v1 URL}"
: "${PDNS_API_KEY:?PDNS_API_KEY must contain the PowerDNS API key}"
: "${TF_COMMAND:?TF_COMMAND must be set to apply or destroy}"
: "${TF_PARALLELISM:?TF_PARALLELISM must be set to a positive integer}"

PDNS_SERVER_URL="${PDNS_SERVER_URL%/}"
export PDNS_SERVER_URL

attempts=60
until curl --fail --silent --show-error \
  --header "X-API-Key: ${PDNS_API_KEY}" \
  "${PDNS_SERVER_URL}/servers" >/dev/null; do
  attempts=$((attempts - 1))
  if [ "${attempts}" -eq 0 ]; then
    >&2 echo "PowerDNS API did not become available at ${PDNS_SERVER_URL}"
    exit 1
  fi

  >&2 echo "Waiting for PowerDNS API at ${PDNS_SERVER_URL}"
  sleep 2
done

terraform init -input=false

case "${TF_COMMAND}" in
  apply|destroy)
    ;;
  *)
    >&2 echo "TF_COMMAND must be either apply or destroy"
    exit 1
    ;;
esac

terraform "${TF_COMMAND}" \
  -auto-approve \
  -input=false \
  -parallelism="${TF_PARALLELISM}"
