# PowerDNS-Admin
# Original from:
# https://github.com/ngoduykhanh/PowerDNS-Admin
#
# Initial image by winggundamth(/powerdns-mysql:trusty)
#
#
FROM alpine
MAINTAINER Jeroen Boonstra <jeroen [at] provider.nl>

ENV APP_USER=web APP_NAME=powerdns-admin
ENV APP_PATH=/home/$APP_USER/$APP_NAME


RUN apk add --update \
    sudo \
    python \
    libxml2 \
    xmlsec \
    git \
    python-dev \
    py-pip \
    build-base  \
    libxml2-dev \
    xmlsec-dev \
    libffi-dev \
    openldap-dev \
  && adduser -S web

RUN sudo -u $APP_USER -H git clone --depth=1 \
      https://github.com/thomasDOTde/PowerDNS-Admin $APP_PATH

RUN pip install -r $APP_PATH/requirements.txt
COPY docker-entrypoint.sh /docker-entrypoint.sh


USER $APP_USER
WORKDIR $APP_PATH
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "run.py"]
EXPOSE 9393
VOLUME ["/var/log"]
