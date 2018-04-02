#!/usr/bin/env bash

IMAGES=(PowerDNS-MySQL PowerDNS-Admin)
for IMAGE in "${IMAGES[@]}"
 do
  echo building $(basename $IMAGE | tr '[A-Z]' '[a-z]')
  cd $IMAGE
  docker build -t $(basename $IMAGE | tr '[A-Z]' '[a-z]') .
  cd ..
done
