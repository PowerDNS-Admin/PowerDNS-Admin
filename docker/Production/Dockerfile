FROM debian:stretch-slim
LABEL maintainer="k@ndk.name"

ENV LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 LANGUAGE=en_US.UTF-8

RUN apt-get update -y \
	&& apt-get install -y --no-install-recommends apt-transport-https locales locales-all python3-pip python3-setuptools python3-dev curl libsasl2-dev libldap2-dev libssl-dev libxml2-dev libxslt1-dev libxmlsec1-dev libffi-dev build-essential libmariadb-dev-compat \
    && curl -sL https://deb.nodesource.com/setup_10.x | bash - \
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list \
    && apt-get update -y \
    && apt-get install -y nodejs yarn \
    && apt-get clean -y \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /opt/powerdns-admin

COPY . .
RUN pip3 install -r requirements.txt \
    && pip3 install psycopg2-binary \
    && yarn install --pure-lockfile \
    && cp config_template.py config.py \
    && flask assets build \
    && rm config.py

COPY ./docker/Production/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV FLASK_APP=app/__init__.py
EXPOSE 80/tcp
ENTRYPOINT ["entrypoint.sh"]
CMD ["gunicorn","app:app"]
