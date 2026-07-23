FROM debian:trixie-slim AS builder
LABEL maintainer="k@ndk.name"

ARG DOCKER_SCENARIO

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    FLASK_APP=powerdnsadmin/__init__.py \
    PATH=/opt/venv/bin:${PATH} \
    YARN_NODE_LINKER=node-modules

# Compilers, headers, Node, and Yarn are build-time dependencies only. The
# runtime stage below receives the completed venv and generated assets.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libldap2-dev \
        libmariadb-dev-compat \
        libpq-dev \
        libsasl2-dev \
        libssl-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libxmlsec1-openssl \
        libxslt1-dev \
        nodejs \
        npm \
        pkg-config \
        python3-dev \
        python3-pip \
        python3-venv \
        yarnpkg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./requirements.txt ./requirements-dev.txt /app/
RUN python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r requirements.txt \
    && if [ "${DOCKER_SCENARIO}" != "docker-dev" ]; then \
        pip install --no-cache-dir -r requirements-dev.txt; \
    fi

COPY . /app

RUN yarnpkg install --immutable --inline-builds \
    && rm -rf /app/powerdnsadmin/static/node_modules \
    && ln -s ../../node_modules /app/powerdnsadmin/static/node_modules \
    && flask assets build \
    # The generated Font Awesome CSS references these public font files.
    && rm /app/powerdnsadmin/static/node_modules \
    && mkdir -p /app/powerdnsadmin/static/node_modules/@fortawesome/fontawesome-free \
    && cp -a /app/node_modules/@fortawesome/fontawesome-free/webfonts \
        /app/powerdnsadmin/static/node_modules/@fortawesome/fontawesome-free/ \
    && rm -rf /app/node_modules /app/.yarn/install-state.gz /root/.cache /root/.yarn


FROM debian:trixie-slim AS runtime
LABEL maintainer="k@ndk.name"

ARG DOCKER_SCENARIO

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    FLASK_APP=powerdnsadmin/__init__.py \
    PATH=/opt/venv/bin:${PATH} \
    POWERDNSADMIN_ASSETS_PREBUILT=1

# Only libraries needed by the compiled Python packages and scenario scripts
# are installed in the final image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libffi8 \
        libldap2 \
        libmariadb3 \
        libpq5 \
        libsasl2-2 \
        libssl3t64 \
        libxml2 \
        libxmlsec1-openssl \
        libxmlsec1t64 \
        libxslt1.1 \
        python3 \
        xmlsec1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app
COPY ./docker-common/wait-for-pdns.sh /opt/wait-for-pdns.sh
COPY ./${DOCKER_SCENARIO}/ /opt/scenario/

RUN mkdir -p /data \
    && chmod u+x /opt/wait-for-pdns.sh /opt/scenario/*.sh

ENTRYPOINT ["/opt/scenario/entrypoint.sh"]
