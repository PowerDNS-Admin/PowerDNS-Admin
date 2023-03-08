This describes how to run Apache2 on the host system with a reverse proxy directing to the docker container

This is usually used to add ssl certificates and prepend a subdirectory

The network_mode host settings is not neccessary but used for ldap availability in this case


docker-compose.yml

```
version: "3"
services:
  app:
    image: powerdnsadmin/pda-legacy:latest
    container_name: powerdns
    restart: always
    network_mode: "host"
    logging:
      driver: json-file
      options:
        max-size: 50m
    environment:
      - BIND_ADDRESS=127.0.0.1:8082
      - SECRET_KEY='NotVerySecret'
      - SQLALCHEMY_DATABASE_URI=mysql://pdnsadminuser:password@127.0.0.1/powerdnsadmin
      - GUNICORN_TIMEOUT=60
      - GUNICORN_WORKERS=2
      - GUNICORN_LOGLEVEL=DEBUG
      - OFFLINE_MODE=False
      - CSRF_COOKIE_SECURE=False
      - SCRIPT_NAME=/powerdns
```

After running the Container create the static directory and populate

```
mkdir -p /var/www/powerdns
docker cp powerdns:/app/powerdnsadmin/static /var/www/powerdns/
chown -R root:www-data /var/www/powerdns
```

Adjust the static reference, static/assets/css has a hardcoded reference

```
sed -i 's/\/static/\/powerdns\/static/' /var/www/powerdns/static/assets/css/*
```

Apache Config:

You can set the SCRIPT_NAME environment using Apache as well, once is sufficient though

```
    <Location /powerdns>
        RequestHeader set X-Forwarded-Proto "https"
        RequestHeader set X-Forwarded-Port "443"
        RequestHeader set SCRIPT_NAME "/powerdns"
        ProxyPreserveHost On
    </Location>

    ProxyPass /powerdns/static !
    ProxyPass /powerdns http://127.0.0.1:8082/powerdns
    ProxyPassReverse /powerdns http://127.0.0.1:8082/powerdns

    Alias /powerdns/static "/var/www/powerdns/static"

    <Directory "/var/www/powerdns/static">
        Options None
        #Options +Indexes
        AllowOverride None
        Order allow,deny
        Allow from all
    </Directory>
```