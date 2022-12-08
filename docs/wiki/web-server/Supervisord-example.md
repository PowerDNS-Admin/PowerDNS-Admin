Following is an example showing how to run PowerDNS-Admin with supervisord

Create supervisord program config file
```
$ sudo vim /etc/supervisor.d/powerdnsadmin.conf
```

```
[program:powerdnsadmin]
command=/opt/web/powerdns-admin/flask/bin/python ./run.py
stdout_logfile=/var/log/supervisor/program_powerdnsadmin.log
stderr_logfile=/var/log/supervisor/program_powerdnsadmin.error
autostart=true
autorestart=true
directory=/opt/web/powerdns-admin
```

Then `sudo supervisorctl start powerdnsadmin` to start the Powerdns-Admin service.