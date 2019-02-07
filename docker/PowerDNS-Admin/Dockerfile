FROM alpine
ARG ENVIRONMENT=development
ENV ENVIRONMENT=${ENVIRONMENT}

WORKDIR /powerdns-admin

RUN set -xe; \
    apk add --no-cache su-exec nodejs python3 mariadb-client mariadb-connector-c yarn netcat-openbsd libldap xmlsec; \
    pip3 install --upgrade pip

COPY ./requirements.txt /powerdns-admin/requirements.txt

RUN set -xe; \
    apk add --no-cache --virtual _build alpine-sdk mariadb-dev libffi-dev xmlsec-dev python3-dev openldap-dev; \
    pip3 install -r requirements.txt; \
    apk del _build

ADD . /powerdns-admin/

RUN set -xe; \
    adduser -Su 50 -s /sbin/nologin www-data; \
    addgroup -Sg 50 www-data; \
    adduser www-data www-data; \
    chown -R www-data:www-data /powerdns-admin/app/static; \
    yarn install --pure-lockfile

ADD ./supervisord.conf /etc/supervisord.conf
COPY ./configs/${ENVIRONMENT}.py /powerdns-admin/config.py
COPY ./docker/PowerDNS-Admin/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]