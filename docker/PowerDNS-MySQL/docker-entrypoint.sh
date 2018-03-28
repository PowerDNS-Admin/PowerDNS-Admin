#!/bin/sh
# Author: Jirayut 'Dear' Nimsaeng
#
set -e

PDNS_CONF_PATH="/etc/powerdns/pdns.conf"
PDNS_MYSQL_CONF_PATH="/etc/powerdns/pdns.d/pdns.mysql.conf"
PDNS_MYSQL_HOST="localhost"
PDNS_MYSQL_PORT="3306"
PDNS_MYSQL_USERNAME="powerdns"
PDNS_MYSQL_PASSWORD="$PDNS_DB_PASSWORD"
PDNS_MYSQL_DBNAME="powerdns"

if [ -z "$PDNS_DB_PASSWORD" ]; then
    echo 'ERROR: PDNS_DB_PASSWORD environment variable not found'
    exit 1
fi

# Configure variables
if [ "$PDNS_DB_HOST" ]; then
    PDNS_MYSQL_HOST="$PDNS_DB_HOST"
fi
if [ "$PDNS_DB_PORT" ]; then
    PDNS_MYSQL_PORT="$PDNS_DB_PORT"
fi
if [ "$PDNS_DB_USERNAME" ]; then
    PDNS_MYSQL_USERNAME="$PDNS_DB_USERNAME"
fi
if [ "$PDNS_DB_NAME" ]; then
    PDNS_MYSQL_DBNAME="$PDNS_DB_NAME"
fi

# Configure mysql backend
sed -i \
    -e "s/^gmysql-host=.*/gmysql-host=$PDNS_MYSQL_HOST/g" \
    -e "s/^gmysql-port=.*/gmysql-port=$PDNS_MYSQL_PORT/g" \
    -e "s/^gmysql-user=.*/gmysql-user=$PDNS_MYSQL_USERNAME/g" \
    -e "s/^gmysql-password=.*/gmysql-password=$PDNS_MYSQL_PASSWORD/g" \
    -e "s/^gmysql-dbname=.*/gmysql-dbname=$PDNS_MYSQL_DBNAME/g" \
    $PDNS_MYSQL_CONF_PATH

if [ "$PDNS_SLAVE" != "1" ]; then
    # Configure to be master
    sed -i \
        -e "s/^#\?\smaster=.*/master=yes/g" \
        -e "s/^#\?\sslave=.*/slave=no/g" \
        $PDNS_CONF_PATH
else
    # Configure to be slave
    sed -i \
        -e "s/^#\?\smaster=.*/master=no/g" \
        -e "s/^#\?\sslave=.*/slave=yes/g" \
        $PDNS_CONF_PATH
fi

if [ "$PDNS_API_KEY" ]; then
    # Enable API
    sed -i \
        -e "s/^#\?\sapi=.*/api=yes/g" \
        -e "s!^#\?\sapi-logfile=.*!api-logfile=/dev/stdout!g" \
        -e "s/^#\?\sapi-key=.*/api-key=$PDNS_API_KEY/g" \
        -e "s/^#\?\swebserver=.*/webserver=yes/g" \
        -e "s/^#\?\swebserver-address=.*/webserver-address=0.0.0.0/g" \
        $PDNS_CONF_PATH
fi

if [ "$PDNS_WEBSERVER_ALLOW_FROM" ]; then
    sed -i \
        "s/^#\?\swebserver-allow-from=.*/webserver-allow-from=$PDNS_WEBSERVER_ALLOW_FROM/g" \
        $PDNS_CONF_PATH
fi


MYSQL_COMMAND="mysql -h $PDNS_MYSQL_HOST -P $PDNS_MYSQL_PORT -u $PDNS_MYSQL_USERNAME -p$PDNS_MYSQL_PASSWORD"

until $MYSQL_COMMAND -e ";" ; do
    >&2 echo "MySQL is unavailable - sleeping"
    sleep 1
done

>&2 echo "MySQL is up - initial database if not exists"
MYSQL_CHECK_IF_HAS_TABLE="SELECT COUNT(DISTINCT table_name) FROM information_schema.columns WHERE table_schema = '$PDNS_MYSQL_DBNAME';"
MYSQL_NUM_TABLE=$($MYSQL_COMMAND --batch --skip-column-names -e "$MYSQL_CHECK_IF_HAS_TABLE")
if [ "$MYSQL_NUM_TABLE" -eq 0 ]; then
    $MYSQL_COMMAND -D $PDNS_MYSQL_DBNAME < /usr/share/doc/pdns-backend-mysql/schema.mysql.sql
fi

# Start PowerDNS
exec "$@"
