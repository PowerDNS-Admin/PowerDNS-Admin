#!/bin/sh

set -e

if [ "$WAITFOR_DB" -a ! -f "$APP_PATH/config.py" ]; then
    cp "$APP_PATH/config_template_docker.py" "$APP_PATH/config.py"
fi

cd $APP_PATH && python create_db.py

# Start PowerDNS Admin
exec "$@"
