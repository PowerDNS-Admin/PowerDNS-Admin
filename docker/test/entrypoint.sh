#!/bin/sh

set -e

coverage_output_dir="${COVERAGE_OUTPUT_DIR:-/test-results/coverage}"
mkdir -p "${coverage_output_dir}"

set -- \
  --cov=powerdnsadmin \
  --cov-config=/app/.coveragerc \
  --cov-report=term-missing:skip-covered \
  "--cov-report=xml:${coverage_output_dir}/coverage.xml" \
  "--cov-report=html:${coverage_output_dir}/html" \
  -W ignore::DeprecationWarning \
  --capture=no \
  -vv

if [ -n "${COVERAGE_FAIL_UNDER:-}" ]; then
  set -- "$@" "--cov-fail-under=${COVERAGE_FAIL_UNDER}"
fi

exec /opt/wait-for-pdns.sh /opt/venv/bin/pytest "$@"
