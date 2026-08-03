ARG PYTHON_FULL_VERSION=3.14.5
ARG PYTHON_PATCH_LEVEL=5

FROM alpine:3.24 AS builder

ARG PYTHON_FULL_VERSION
ARG PYTHON_PATCH_LEVEL

ARG BUILD_DEPENDENCIES="build-base \
    libffi-dev \
    libpq-dev \
    libxml2-dev \
    mariadb-connector-c-dev \
    openldap-dev \
    python3-dev \
    xmlsec-dev \
    npm \
    cargo"

ENV LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    FLASK_APP=/build/powerdnsadmin/__init__.py \
    PATH=/opt/venv/bin:${PATH}

RUN apk add --no-cache ${BUILD_DEPENDENCIES} && \
    apk add --no-cache py3-pip && \
    npm install --global corepack@0.35.0 && \
    corepack enable && \
    python3 -m venv /opt/venv && \
    test "$(python3 -c 'import platform; print(platform.python_version())')" = "${PYTHON_FULL_VERSION}" && \
    test "$(python3 -c 'import sys; print(sys.version_info.micro)')" = "${PYTHON_PATCH_LEVEL}"

WORKDIR /build

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /build/requirements.txt

# Get application dependencies
RUN pip install --upgrade pip && \
    pip install --use-pep517 -r requirements.txt

# Add sources
COPY . /build

# Prepare assets
RUN YARN_NODE_LINKER=node-modules yarn install --immutable --inline-builds && \
    rm -rf /build/powerdnsadmin/static/node_modules && \
    ln -s ../../node_modules /build/powerdnsadmin/static/node_modules && \
    flask assets build && \
    rm /build/powerdnsadmin/static/node_modules

RUN mv /build/powerdnsadmin/static /tmp/static && \
    mkdir /build/powerdnsadmin/static && \
    cp -r /tmp/static/generated /build/powerdnsadmin/static && \
    cp -r /tmp/static/assets /build/powerdnsadmin/static && \
    cp -r /tmp/static/img /build/powerdnsadmin/static && \
    mkdir -p /build/powerdnsadmin/static/node_modules/@fortawesome/fontawesome-free && \
    cp -a /build/node_modules/@fortawesome/fontawesome-free/webfonts \
        /build/powerdnsadmin/static/node_modules/@fortawesome/fontawesome-free/

RUN { \
      echo "from flask_assets import Environment"; \
      echo "assets = Environment()"; \
      echo "assets.register('js_login', 'generated/login.js')"; \
      echo "assets.register('css_login', 'generated/login.css')"; \
      echo "assets.register('js_main', 'generated/main.js')"; \
      echo "assets.register('css_main', 'generated/main.css')"; \
    } > /build/powerdnsadmin/assets.py

# Move application
RUN mkdir -p /app && \
    cp -r /build/migrations/ /build/powerdnsadmin/ /build/run.py /app && \
    mkdir -p /app/configs && \
    cp -r /build/configs/docker_config.py /app/configs

# Build image
FROM alpine:3.24

ARG PYTHON_FULL_VERSION
ARG PYTHON_PATCH_LEVEL

LABEL org.powerdnsadmin.image.python.version="${PYTHON_FULL_VERSION}" \
      org.powerdnsadmin.image.python.patch-level="${PYTHON_PATCH_LEVEL}"

ENV FLASK_APP=/app/powerdnsadmin/__init__.py \
    PATH=/opt/venv/bin:${PATH} \
    USER=pda

RUN apk add --no-cache mariadb-connector-c postgresql-client py3-gunicorn py3-pyldap py3-flask py3-psycopg2 xmlsec tzdata libcap && \
    addgroup -S ${USER} && \
    adduser -S -D -G ${USER} ${USER} && \
    mkdir /data && \
    chown ${USER}:${USER} /data && \
    setcap cap_net_bind_service=+ep $(readlink -f /usr/bin/python3) && \
    apk del libcap && \
    test "$(python3 -c 'import platform; print(platform.python_version())')" = "${PYTHON_FULL_VERSION}" && \
    test "$(python3 -c 'import sys; print(sys.version_info.micro)')" = "${PYTHON_PATCH_LEVEL}"

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=root:${USER} /app /app/
COPY ./docker/entrypoint.sh /usr/bin/

WORKDIR /app
RUN chown ${USER}:${USER} ./configs /app && \
    cat ./powerdnsadmin/default_config.py ./configs/docker_config.py > ./powerdnsadmin/docker_config.py

EXPOSE 80/tcp
USER ${USER}
HEALTHCHECK --interval=5s --timeout=5s --start-period=20s --retries=5 CMD wget --output-document=- --quiet --tries=1 http://127.0.0.1${SCRIPT_NAME:-/}healthcheck
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn","powerdnsadmin:create_app()"]
