FROM debian:trixie-slim
LABEL maintainer="k@ndk.name"

ENV LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        apt-transport-https \
        curl \
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
        locales \
        locales-all \
        pkg-config \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-venv \
    #&& curl -sL https://deb.nodesource.com/setup_lts.x | bash - \
    #&& curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    #&& echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list \
    #&& apt-get update -y \
    && apt-get install -y --no-install-recommends \
        nodejs \
        npm \
        yarnpkg \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
#RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app
RUN mkdir -p /data

ENV FLASK_APP=powerdnsadmin/__init__.py
ENV POWERDNS_ADMIN_MODE=dev
ENV YARN_NODE_LINKER=node-modules
RUN yarnpkg install --immutable --inline-builds \
    && yarnpkg cache clean \
    && rm -rf /app/powerdnsadmin/static/node_modules \
    && ln -s ../../node_modules powerdnsadmin/static/node_modules \
    && flask assets build

COPY ./docker-test/docker-entrypoint.sh ./docker-test/wait-for-pdns.sh /opt/
RUN chmod u+x /opt/docker-entrypoint.sh /opt/wait-for-pdns.sh
ENTRYPOINT ["/opt/docker-entrypoint.sh"]
