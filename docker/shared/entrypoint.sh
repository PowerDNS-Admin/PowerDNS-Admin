#!/bin/sh
set -e

script_path=$(readlink -f "$0")
app_path=$(dirname $(dirname $(dirname "$script_path")))
docker_path=$app_path/docker
first_run_path=$docker_path/.firstrun

########################################################################################################################
# START CONFIGURATION
########################################################################################################################

# How many seconds to wait after a connection attempt failure before trying again
PDA_CHECK_MYSQL_FAIL_DELAY=${PDA_CHECK_MYSQL_FAIL_DELAY:-2}

# How many seconds to wait after a successful connection attempt before proceeding to the next step
PDA_CHECK_MYSQL_SUCCESS_DELAY=${PDA_CHECK_MYSQL_SUCCESS_DELAY:-0}

# How many MySQL connection attempts should be made before halting container execution
PDA_CHECK_MYSQL_ATTEMPTS=${PDA_CHECK_MYSQL_ATTEMPTS:-30}

# How many seconds to wait after a connection attempt failure before trying again
PDA_CHECK_API_FAIL_DELAY=${PDA_CHECK_API_FAIL_DELAY:-2}

# How many seconds to wait after a successful connection attempt before proceeding to the next step
PDA_CHECK_API_SUCCESS_DELAY=${PDA_CHECK_API_SUCCESS_DELAY:-0}

# How many API connection attempts should be made before halting container execution
PDA_CHECK_API_ATTEMPTS=${PDA_CHECK_API_ATTEMPTS:-15}

PDA_GUNICORN_BIND_ADDRESS="${PDA_GUNICORN_BIND_ADDRESS:-0.0.0.0:80}"

PDA_GUNICORN_TIMEOUT="${PDA_GUNICORN_TIMEOUT:-120}"

PDA_GUNICORN_WORKERS="${PDA_GUNICORN_WORKERS:-4}"

PDA_GUNICORN_LOGLEVEL="${PDA_GUNICORN_LOGLEVEL:-info}"

########################################################################################################################
# END CONFIGURATION
########################################################################################################################

API_URI="${PDA_PDNS_PROTO:-http}://${PDA_PDNS_HOST:-127.0.0.1}:${PDA_PDNS_PORT:-8081}/api/v1/servers"
API_AUTH_HEADER="X-API-Key: ${PDA_PDNS_API_KEY}"
GUNICORN_ARGS="-t ${PDA_GUNICORN_TIMEOUT} --workers ${PDA_GUNICORN_WORKERS} --log-level ${PDA_GUNICORN_LOGLEVEL}  \
--bind ${PDA_GUNICORN_BIND_ADDRESS}"

convert_file_vars() {
    for line in $(env); do
        if [[ $line == PDA_* ]] || [[ $line == AS_* ]]; then
            if [[ $line =~ ^.*_FILE ]]; then
                local INDEX=$(echo $line | grep -aob '=' | grep -oE '[0-9]+')
                local LEN=$(echo $line | wc -c)
                local NAME_END_INDEX=$(($INDEX - 5))
                local NAME_FULL=$(echo $line | cut -c1-$INDEX)
                local NAME=$(echo $line | cut -c1-$NAME_END_INDEX)
                INDEX=$(($INDEX + 2))
                local VALUE=$(echo $line | cut -c$INDEX-$LEN)
                local FILE_VALUE=$(cat $VALUE)
                export $NAME=$FILE_VALUE
                unset $NAME_FULL
            fi
        fi
    done
}

verify_mysql_ready() {
    local host=$1
    local port=$2
    local retry_executed=1

    while ! nc -z $host $port >& /dev/null; do
        # The last connection test to the MySQL server failed at this point

        # If the remaining retry counter falls to zero, exit the connection test cycle
        if [ $retry_executed -ge $PDA_CHECK_MYSQL_ATTEMPTS ]; then
            echo "The maximum number ($PDA_CHECK_MYSQL_ATTEMPTS) of TCP connection tests have been executed without success. This container will now exit."
            exit 1
        else
            echo "MySQL server is offline. The TCP connection test cycle number $retry_executed has failed to $host:$port. Waiting for $PDA_CHECK_MYSQL_FAIL_DELAY seconds..."
        fi

        # Delay execution for the configured MySQL fail delay
        sleep $PDA_CHECK_MYSQL_FAIL_DELAY

        # Increment the retry execution counter
        retry_executed=$((retry_executed + 1))
    done

    echo "MySQL server is online after $retry_executed check(s). Delaying execution for $PDA_CHECK_MYSQL_SUCCESS_DELAY seconds..."

    sleep $PDA_CHECK_MYSQL_SUCCESS_DELAY
}

verify_api_ready() {
    local retry_executed=1

    while [ $(curl -s -o /dev/null -w "%{http_code}" -H "$2" $1) -ne "200" ]; do
        # The last connection test to the API server failed at this point

        # If the remaining retry counter falls to zero, exit the connection test cycle
        if [ $retry_executed -ge $PDA_CHECK_API_ATTEMPTS ]; then
            echo "The maximum number ($PDA_CHECK_API_ATTEMPTS) of API server HTTP connection tests have been executed without success. This container will now exit."
            exit 1
        else
            echo "PowerDNS API server is offline. The HTTP connection test cycle number $retry_executed has failed to $1. Waiting for $PDA_CHECK_API_FAIL_DELAY seconds..."
        fi

        # Delay execution for the configured API fail delay
        sleep $PDA_CHECK_API_FAIL_DELAY

        # Increment the retry execution counter
        retry_executed=$((retry_executed + 1))
    done

    echo "PowerDNS API server is online after $retry_executed check(s). Delaying execution for ${PDA_CHECK_API_SUCCESS_DELAY} seconds..."

    sleep $PDA_CHECK_API_SUCCESS_DELAY
}

first_run() {
    # Determine if the first run file exists and abort if so
    if [ -f "$first_run_path" ]; then
        echo "First run actions aborting as a first run file exists at $first_run_path"
        return
    fi

    # Assume MySQL database if the SQLA_DB_HOST environment variable has been set, otherwise assume SQLite
    if [ -n "$SQLA_DB_HOST" ]; then
        table=tsigkeys
        sql_exists=$(printf 'SHOW TABLES LIKE "%s"' "$table")
        if [[ -z $(mysql -h $SQLA_DB_HOST -u $SQLA_DB_USER -p$SQLA_DB_PASSWORD -e "$sql_exists" $SQLA_DB_NAME) ]]; then
            echo "The table $table does not exist so the base pdns schema will be installed."
            mysql_result=$(mysql -h $SQLA_DB_HOST -u $SQLA_DB_USER -p$SQLA_DB_PASSWORD $SQLA_DB_NAME < /srv/app/docker/shared/pdns-schema-mysql.sql)
        else
            echo "The table $table does exist so no further action will be taken."
        fi
    fi

    if [ ! -f "/srv/app/pdns.db" ]; then
        cat /srv/app/docker/shared/pdns-schema-sqlite.sql | sqlite3 /srv/app/pdns.db
    fi

    touch $first_run_path;
}

# If the command starts with an option, prepend the appropriate command name
if [ "${1:0:1}" = '-' ]; then
    set -- "gunicorn" "$@"
fi

# Automatically convert any environment variables that are prefixed with "PDA_" or "AS_" and suffixed with "_FILE"
convert_file_vars

# Verify that the configured MySQL server is ready for connections
if [ -n "$SQLA_DB_HOST" ]; then
    verify_mysql_ready "${SQLA_DB_HOST}" "${SQLA_DB_PORT:-3306}"
fi

# Execute first run tasks
# - Setup the base PowerDNS Authoritative server database schema if this is the first run
first_run

# Verify that the configured PowerDNS name server API is ready for connections
if [ -n "$PDA_PDNS_HOST" ]; then
    verify_api_ready "${API_URI}" "${API_AUTH_HEADER}"
fi

echo "Proceeding with app initialization..."
cd /srv/app

# Execute any pending database upgrades via Flask
flask db upgrade

if [ $FLASK_ENV = "development" ]; then
    yarn install --pure-lockfile --${FLASK_ENV}
    yarn cache clean
    flask assets build
fi

# Determine if the gunicorn command is being used and append program arguments if so. Otherwise, execute normally
if [ "$1" = "gunicorn" ]; then
    exec "$@" $GUNICORN_ARGS
else
    exec "$@"
fi
