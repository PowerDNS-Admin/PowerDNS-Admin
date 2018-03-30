FROM ubuntu:latest
MAINTAINER Khanh Ngo "ngokhanhit@gmail.com"
ARG ENVIRONMENT=development
ENV ENVIRONMENT=${ENVIRONMENT}

WORKDIR /powerdns-admin

RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev libmysqlclient-dev supervisor
RUN apt-get install -y libsasl2-dev libldap2-dev libssl-dev

COPY ./requirements.txt /powerdns-admin/requirements.txt
RUN pip3 install -r requirements.txt

ADD ./supervisord.conf /etc/supervisord.conf
ADD . /powerdns-admin/
COPY ./configs/${ENVIRONMENT}.py /powerdns-admin/config.py
