FROM debian:bullseye-slim
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
    && curl -sL https://deb.nodesource.com/setup_lts.x | bash - \
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        nodejs \
        yarn \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /app

ENV FLASK_APP=powerdnsadmin/__init__.py
RUN yarn install --pure-lockfile --production \
    && yarn cache clean \
    && flask assets build

COPY ./docker-test/wait-for-pdns.sh /opt
RUN chmod u+x /opt/wait-for-pdns.sh
CMD ["/opt/wait-for-pdns.sh", "/usr/local/bin/pytest", "-W", "ignore::DeprecationWarning", "--capture=no", "-vv"]
