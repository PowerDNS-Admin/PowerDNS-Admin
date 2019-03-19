#!/bin/sh

set -e

LOOPS=100
COUNTER=1
until curl -L "http://${PDA_HOST}:9191"|grep "Create an account "; do
  >&2 echo "PowerDNS Admin is unavailable - sleeping"
  sleep 3
  if [ $LOOPS -eq $COUNTER ]
  then
    exit 134
  fi
  COUNTER=$(( $COUNTER + 1 ))
done

sleep 5

>&2 echo "PowerDNS Admin is up - executing command"
