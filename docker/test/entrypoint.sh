#!/bin/sh

set -e

coverage_output_dir="${COVERAGE_OUTPUT_DIR:-/test-results/coverage}"
mkdir -p "${coverage_output_dir}"

# The shared app image defaults CMD to gunicorn. Ignore that for the test
# scenario so `docker compose up` still runs the full pytest suite, while
# preserving explicit pytest paths from `docker compose run ... tests/smoke`.
if [ "$#" -eq 0 ] || [ "$1" = "gunicorn" ]; then
  set --
fi

set -- \
  --cov=powerdnsadmin \
  --cov-config=/app/.coveragerc \
  --cov-report=term-missing:skip-covered \
  "--cov-report=xml:${coverage_output_dir}/coverage.xml" \
  "--cov-report=html:${coverage_output_dir}/html" \
  -W ignore::DeprecationWarning \
  --capture=no \
  -vv \
  "$@"

if [ -n "${COVERAGE_FAIL_UNDER:-}" ]; then
  set -- "$@" "--cov-fail-under=${COVERAGE_FAIL_UNDER}"
fi

exec /opt/wait-for-pdns.sh /opt/venv/bin/pytest "$@"
