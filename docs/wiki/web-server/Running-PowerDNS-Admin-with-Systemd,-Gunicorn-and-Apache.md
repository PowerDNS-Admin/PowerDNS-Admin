Following is an example showing how to run PowerDNS-Admin with systemd, gunicorn and Apache:

The systemd and gunicorn setup are the same as for with nginx.  This set of configurations assumes you have installed your PowerDNS-Admin under /opt/powerdns-admin and are running with a package-installed gunicorn.

## Configure systemd service

`$ sudo vim /etc/systemd/system/powerdns-admin.service`

```
[Unit]
Description=PowerDNS web administration service
Requires=powerdns-admin.socket
Wants=network.target
After=network.target mysqld.service postgresql.service slapd.service mariadb.service

[Service]
PIDFile=/run/powerdns-admin/pid
User=pdnsa
Group=pdnsa
WorkingDirectory=/opt/powerdns-admin
ExecStart=/usr/bin/gunicorn-3.6 --workers 4 --log-level info --pid /run/powerdns-admin/pid --bind unix:/run/powerdns-admin/socket "powerdnsadmin:create_app(config='config.py')"
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
PrivateTmp=true
Restart=on-failure
RestartSec=10
StartLimitInterval=0

[Install]
WantedBy=multi-user.target
```

`$ sudo vim /etc/systemd/system/powerdns-admin.socket`

```
[Unit]
Description=PowerDNS-Admin socket

[Socket]
ListenStream=/run/powerdns-admin/socket

[Install]
WantedBy=sockets.target
```

`$ sudo vim /etc/tmpfiles.d/powerdns-admin.conf`

```
d /run/powerdns-admin 0755 pdnsa pdnsa -
```

Then `sudo systemctl daemon-reload; sudo systemctl start powerdns-admin.socket; sudo systemctl enable powerdns-admin.socket` to start the Powerdns-Admin service and make it run on boot.

## Sample Apache configuration 

This includes SSL redirect.

```
<VirtualHost *:80>
  ServerName dnsadmin.company.com
  DocumentRoot "/opt/powerdns-admin"
  <Directory "/opt/powerdns-admin">
    Options Indexes FollowSymLinks MultiViews
    AllowOverride None
    Require all granted
  </Directory>
  Redirect permanent / https://dnsadmin.company.com/
</VirtualHost>
<VirtualHost *:443>
  ServerName dnsadmin.company.com
  DocumentRoot "/opt/powerdns-admin/powerdnsadmin"
  ## Alias declarations for resources outside the DocumentRoot
  Alias /static/ "/opt/powerdns-admin/powerdnsadmin/static/"
  Alias /favicon.ico "/opt/powerdns-admin/powerdnsadmin/static/favicon.ico"
  <Directory "/opt/powerdns-admin">
    AllowOverride None
    Require all granted
  </Directory>
  ## Proxy rules
  ProxyRequests Off
  ProxyPreserveHost On
  ProxyPass /static/ !
  ProxyPass /favicon.ico !
  ProxyPass / unix:/var/run/powerdns-admin/socket|http://%{HTTP_HOST}/
  ProxyPassReverse / unix:/var/run/powerdns-admin/socket|http://%{HTTP_HOST}/
  ## SSL directives
  SSLEngine on
  SSLCertificateFile      "/etc/pki/tls/certs/dnsadmin.company.com.crt"
  SSLCertificateKeyFile   "/etc/pki/tls/private/dnsadmin.company.com.key"
</VirtualHost>
```

## Notes
* The above assumes your installation is under /opt/powerdns-admin
* The hostname is assumed as dnsadmin.company.com
* gunicorn is installed in /usr/bin via a package (as in the case with CentOS/Redhat 7) and you have Python 3.6 installed.  If you prefer to use flask then see the systemd configuration for nginx.
* On Ubuntu / Debian systems, you may need to enable the "proxy_http" module with `a2enmod proxy_http`
