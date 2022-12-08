## Configure systemd service

This example uses package-installed gunicorn (instead of flask-installed) and PowerDNS-Admin installed under /opt/powerdns-admin

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
d /run/powerdns-admin 0755 pdns pdns -
```

Then `sudo systemctl daemon-reload; sudo systemctl start powerdns-admin.socket; sudo systemctl enable powerdns-admin.socket` to start the Powerdns-Admin service and make it run on boot.
