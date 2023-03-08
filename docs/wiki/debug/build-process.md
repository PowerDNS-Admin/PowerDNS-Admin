This discribes how to debug the buildprocess 


docker-compose.yml

```
version: "3"
services:
  app:
    image: powerdns/custom
    container_name: powerdns
    restart: always
    build:
        context: git
        dockerfile: docker/Dockerfile
    network_mode: "host"
    logging:
      driver: json-file
      options:
        max-size: 50m
    environment:
      - BIND_ADDRESS=127.0.0.1:8082
      - SECRET_KEY='VerySecret'
      - SQLALCHEMY_DATABASE_URI=mysql://pdnsadminuser:password@127.0.0.1/powerdnsadmin
      - GUNICORN_TIMEOUT=60
      - GUNICORN_WORKERS=2
      - GUNICORN_LOGLEVEL=DEBUG
      - OFFLINE_MODE=False
      - CSRF_COOKIE_SECURE=False
```

Create a git folder in the location of the `docker-compose.yml` and clone the repo into it

```
mkdir git
cd git 
git clone https://github.com/PowerDNS-Admin/PowerDNS-Admin.git .
```

In case you are behind an SSL Filter like me, you can add the following to each stage of the `git/docker/Dockerfile`

This installs the command `update-ca-certificates` from the alpine repo and adds an ssl cert to the trust chain, make sure you are getting the right version in case the base image version changes

```
RUN mkdir /tmp-pkg && cd /tmp-pkg && wget http://dl-cdn.alpinelinux.org/alpine/v3.17/main/x86_64/ca-certificates-20220614-r4.apk && apk add --allow-untrusted --no-network --no-cache /tmp-pkg/ca-certificates-20220614-r4.apk || true
RUN rm -rf /tmp/pkg
COPY MyCustomCerts.crt /usr/local/share/ca-certificates/MyCustomCerts.crt
RUN update-ca-certificates
COPY pip.conf /etc/pip.conf
```

`MyCustomCerts.crt` and `pip.conf` have to be placed inside the `git` folder.

The content of `pip.conf` is:

```
[global]
cert = /usr/local/share/ca-certificates/MyCustomCerts.crt
```

For easier debugging you can change the `CMD` of the `Dockerfile` to `CMD ["tail","-f", "/dev/null"]` though I expect you to be fluent in Docker in case you wish to debug