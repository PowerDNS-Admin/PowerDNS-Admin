FROM alpine
ARG ENVIRONMENT=development
ENV ENVIRONMENT=${ENVIRONMENT}

WORKDIR /powerdns-admin

RUN set -xe; \
    apk add --no-cache su-exec nodejs python3 mariadb-client mariadb-connector-c yarn netcat-openbsd libldap xmlsec; \
    pip3 install --upgrade pip

COPY ./requirements.txt /powerdns-admin/requirements.txt

RUN set -xe; \
    apk add py3-flask py3-flask-login py-flask-assets py3-mysqlclient py3-configobj py3-bcrypt py3-dnspython py3-gunicorn py3-openssl py3-pytest py3-yaml py3-urllib3 py3-lxml py3-jsonschema py3-simplejson py3-chardet py3-asn1 py3-certifi py3-defusedxml py3-asn1-modules py3-dateutil py3-mako py3-webcolors; \
    apk add --no-cache --virtual _build alpine-sdk mariadb-dev libffi-dev xmlsec-dev python3-dev openldap-dev; \
    pip3 install -r requirements.txt; \
    apk del _build

COPY . /powerdns-admin/

RUN set -xe; \
    adduser -Su 50 -s /sbin/nologin www-data; \
    addgroup -Sg 50 www-data; \
    adduser www-data www-data; \
    chown -R www-data:www-data /powerdns-admin/app/static; \
    yarn install --pure-lockfile

RUN set -xe; \
    sed -i "s%^\(LOG_FILE\).*$%\1 = 'logs/logfile.log'%" config_template.py; \
    install -d -m 755 -o www-data -g www-data logs; \
    sed -e 's/^# \(SQLALCHEMY_DATABASE_URI.*\)$/\1/' config_template.py > config.py; \
    ln -fs ../../node_modules app/static/node_modules; \
    su-exec www-data flask assets build; \
    rm config.py

COPY ./supervisord.conf /etc/supervisord.conf
COPY ./configs/${ENVIRONMENT}.py /powerdns-admin/config.py
COPY ./docker/PowerDNS-Admin/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]