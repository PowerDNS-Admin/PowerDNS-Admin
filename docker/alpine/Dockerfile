ARG DISTRO=alpine
ARG DISTRO_TAG=3.14

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
# - Install required APK packages per the required dependencies
# - Upgrade Python pip package using pip3
RUN apk update \
    && apk add --no-cache curl build-base tzdata libcap libffi-dev libxml2-dev xmlsec-dev mariadb-connector-c-dev \
    openldap-dev python3-dev py3-pip py3-gunicorn py3-psycopg2 yarn cargo mysql-client postgresql-client sqlite \
    && pip install --upgrade pip

# Copy Python pip requirements file for early installation which leverages the image caching mechanisms
COPY /requirements.txt /srv/app/requirements.txt

# Change the working directory which may affect the build contexts of following commands
WORKDIR /srv/app

# Install the required Python pip packages as defined in the ./requirements.txt file
RUN pip install -r requirements.txt

# Copy all project files into the container's /app directory
# FIXME: This is too broad and will almost guarentee constant image re-builds that can be skipped in dev environment
COPY . /srv/app

# Perform the following tasks:
# - Create system group and user as configured in the PDA_GROUP and PDA_USER environment variables
# - Copy additional automation scripts to their appropriate locations
# - Set permissions on automation scripts
# - Install Yarn and clean the Yarn cache
# - Build Flask assets
# - Apply netcaps and cleanup APK packages
RUN addgroup -S --gid $PDA_GID $PDA_GROUP \
    && adduser -S -D --uid $PDA_UID -G $PDA_GROUP $PDA_USER \
    # XXX: Is this setcap still needed?
    && setcap cap_net_bind_service=+ep $(readlink -f /usr/bin/python3) \
    && apk del libcap \
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
