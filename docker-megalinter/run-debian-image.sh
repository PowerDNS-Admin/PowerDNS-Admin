#!/usr/bin/env bash

set -euo pipefail

readonly script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly repository_root="$(cd "${script_dir}/.." && pwd)"
readonly compose_file="${repository_root}/docker-compose-megalinter.yml"

mkdir -p "${repository_root}/test-results/megalinter"

exit_code=0
docker compose \
    --file "${compose_file}" \
    up \
    --build \
    --abort-on-container-exit \
    --exit-code-from megalinter || exit_code=$?

docker compose \
    --file "${compose_file}" \
    down \
    --volumes

exit "${exit_code}"
