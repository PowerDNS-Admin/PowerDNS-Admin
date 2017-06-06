#!/bin/sh

./create_db.py

gunicorn -b 0.0.0.0:${PORT} --access-logfile=/dev/stdout app:app
