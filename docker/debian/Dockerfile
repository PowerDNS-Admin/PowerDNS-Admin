FROM debian:11.1-slim
LABEL maintainer="matt@azorian.solutions"

# Set additional container environment variables
ENV LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    FLASK_APP=${FLASK_APP:-/app/run.py}

# Perform the following tasks:
# - Install required APT packages per the required dependencies
# - Download and execute NodeSource setup package
# - Download and add Yarn public GPG key to APT
# - Add Yarn repository to the APT configuration
# - Update APT cache
# - Install NodeJS and Yarn APT packages
# - Clean APT caches and dynamic lists
# - Upgrade Python pip package using pip3
RUN apt update -y \
    && apt install -y --no-install-recommends apt-transport-https locales locales-all python3-pip python3-setuptools \
    python3-dev curl libsasl2-dev libldap2-dev libssl-dev libxml2-dev libxmlsec1 libxslt1-dev libxmlsec1-dev xmlsec1 \
    libffi-dev build-essential libmariadb-dev-compat pkg-config \
    && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list \
    && apt update -y \
    && apt install -y nodejs yarn \
    && apt clean -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --upgrade pip

# We copy just the requirements.txt first to leverage Docker cache
COPY /requirements.txt /app/requirements.txt

# Change the working directory which may affect the build contexts of following commands
WORKDIR /app

# Install the required Python pip packages as defined in the ./requirements.txt file
RUN pip3 install -r requirements.txt

# Copy all project files into the container's /app directory
# FIXME: This is too broad and will almost guarentee constant image re-builds that can be skipped in dev environment
COPY . /app

# Perform the following tasks:
# - Copy additional automation scripts to their appropriate locations
# - Set permissions on automation scripts
# - Install Yarn and clean the Yarn cache
# - Build Flask assets
RUN cp /app/docker/debian/entrypoint.sh /usr/local/bin/entrypoint.sh \
    && cp /app/docker/debian/pdns-check.sh /srv/ \
    && chmod +x /usr/local/bin/entrypoint.sh /srv/pdns-check.sh \
    && yarn install --pure-lockfile --production \
    && yarn cache clean \
    && flask assets build

# Set the default command of the container to the PDNS check script to prevent premature execution 乁༼ ☯‿☯༽ㄏ
CMD ["/srv/pdns-check.sh", "/usr/local/bin/entrypoint.sh", "/app/run.py"]
