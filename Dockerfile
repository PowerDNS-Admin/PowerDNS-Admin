FROM python:2.7-alpine

ENV PORT 80

RUN mkdir -p /src
COPY requirements.txt /src/

RUN apk add --no-cache libldap libffi mariadb-dev
RUN apk add --no-cache --virtual .fetch-deps  \
        gcc \
        make \
        libc-dev \
        libffi-dev \
        python-dev \
        openldap-dev \
        && pip install --no-cache-dir -r /src/requirements.txt \
        && apk del .fetch-deps

WORKDIR /src

RUN pip install gunicorn==19.6.0

COPY .  /src

CMD /src/docker-entrypoint.sh
