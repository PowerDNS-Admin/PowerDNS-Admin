***
**WARNING**
This just uses the development server for testing purposes. For production environments you should probably go with a more robust solution, like [gunicorn](web-server/Running-PowerDNS-Admin-with-Systemd,-Gunicorn--and--Nginx.md) or a WSGI server.
***

### Following example shows a systemd unit file that can run PowerDNS-Admin

You shouldn't run PowerDNS-Admin as _root_, so let's start of with the user/group creation that will later run PowerDNS-Admin:

Create a new group for PowerDNS-Admin:

> sudo groupadd powerdnsadmin

Create a user for PowerDNS-Admin:

> sudo useradd --system -g powerdnsadmin powerdnsadmin

_`--system` creates a user without login-shell and password, suitable for running system services._

Create new systemd service file:

> sudo vim /etc/systemd/system/powerdns-admin.service

General example:
```
[Unit]
Description=PowerDNS-Admin
After=network.target

[Service]
Type=simple
User=powerdnsadmin
Group=powerdnsadmin
ExecStart=/opt/web/powerdns-admin/flask/bin/python ./run.py
WorkingDirectory=/opt/web/powerdns-admin
Restart=always

[Install]
WantedBy=multi-user.target
```

Debian example:
```
[Unit]
Description=PowerDNS-Admin
After=network.target

[Service]
Type=simple
User=powerdnsadmin
Group=powerdnsadmin
Environment=PATH=/opt/web/powerdns-admin/flask/bin
ExecStart=/opt/web/powerdns-admin/flask/bin/python /opt/web/powerdns-admin/run.py
WorkingDirectory=/opt/web/powerdns-admin
Restart=always

[Install]
WantedBy=multi-user.target
```
Before starting the service, we need to make sure that the new user can work on the files in the PowerDNS-Admin folder:
> chown -R powerdnsadmin:powerdnsadmin /opt/web/powerdns-admin

After saving the file, we need to reload the systemd daemon:
> sudo systemctl daemon-reload

We can now try to start the service:
> sudo systemctl start powerdns-admin

If you would like to start PowerDNS-Admin automagically at startup enable the service:
> systemctl enable powerdns-admin

Should the service not be up by now, consult your syslog. Generally this will be a file permission issue, or python not finding it's modules. See the Debian unit example to see how you can use systemd in a python `virtualenv`