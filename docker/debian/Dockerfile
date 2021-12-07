ARG DISTRO=debian
ARG DISTRO_TAG=11.1-slim

FROM ${DISTRO}:${DISTRO_TAG}
LABEL maintainer="matt@azorian.solutions"

# Set additional container environment variables
ENV LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    PDA_PORT=${PDA_PORT:-80} \
    PDA_UID=${PDA_UID:-1000} \
    PDA_USER=${PDA_USER:-pda} \
    PDA_GID=${PDA_GID:-1000} \
    PDA_GROUP=${PDA_GROUP:-pda} \
    FLASK_APP=${FLASK_APP:-/srv/app/run.py}

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
    libffi-dev build-essential libmariadb-dev-compat pkg-config mysql-client postgresql-client sqlite3 \
    && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
    && curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
    && echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list \
    && apt update -y \
    && apt install -y nodejs yarn \
    && apt clean -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --upgrade pip

# Copy Python pip requirements file for early installation which leverages the image caching mechanisms
COPY /requirements.txt /srv/app/requirements.txt

# Change the working directory which may affect the build contexts of following commands
WORKDIR /srv/app

# Install the required Python pip packages as defined in the ./requirements.txt file
RUN pip3 install -r requirements.txt

# Copy all project files into the container's /srv/app directory
# FIXME: This is too broad and will almost guarentee constant image re-builds that can be skipped in dev environment
COPY . /srv/app

# Perform the following tasks:
# - Copy additional automation scripts to their appropriate locations
# - Set permissions on automation scripts
# - Install Yarn and clean the Yarn cache
# - Build Flask assets
RUN addgroup --system --gid $PDA_GID $PDA_GROUP \
    && adduser --system --disabled-login --no-create-home --home /tmp --shell /bin/false --uid $PDA_UID \
    --ingroup $PDA_GROUP $PDA_USER 2>/dev/null \
    && yarn install --pure-lockfile --production \
    && yarn cache clean \
    && flask assets build

# Set the system user and group for the primary container process
USER "${PDA_USER}:${PDA_GROUP}"

# Define the app directory as a volume
VOLUME /srv/app

# Expose the configured service port
EXPOSE 80/TCP

# Set the entrypoint script of the container
ENTRYPOINT ["sh", "/srv/app/docker/shared/entrypoint.sh"]

# Set the default command of the container to be ran following the entrypoint script
CMD ["sh", "-c", "/srv/app/run.py"]
