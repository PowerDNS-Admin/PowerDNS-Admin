# uWSGI Example

This guide will show you how to run PowerDNS-Admin via uWSGI and nginx. This guide was written using Debian 8 with the following software versions:
- nginx 1.6.2
- uwsgi 2.0.7-debian
- python 2.7.9

## Software installation:

1. apt install the following packages:
   - `uwsgi`
   - `uwsgi-plugin-python`
   - `nginx`

## Step-by-step instructions
1. Create a uWSGI .ini in `/etc/uwsgi/apps-enabled` with the following contents, making sure to replace the chdir, pythonpath and virtualenv directories with where you've installed PowerDNS-Admin:
 ```ini
 [uwsgi]
 plugins = python27
 
 uid=www-data
 gid=www-data
 
 chdir = /opt/pdns-admin/PowerDNS-Admin/
 pythonpath = /opt/pdns-admin/PowerDNS-Admin/
 virtualenv = /opt/pdns-admin/PowerDNS-Admin/flask 
 
 mount = /pdns=powerdnsadmin:create_app()
 manage-script-name = true
 
 vacuum = true
 harakiri = 20
 buffer-size = 32768
 post-buffering = 8192
 socket = /run/uwsgi/app/%n/%n.socket
 chown-socket = www-data
 pidfile = /run/uwsgi/app/%n/%n.pid 
 
 daemonize = /var/log/uwsgi/app/%n.log
 enable-threads
 ```
2. Add the following configuration to your nginx config:
 ```nginx
 location / { try_files $uri @pdns_admin; } 

 location @pdns_admin {
     include uwsgi_params;
     uwsgi_pass unix:/run/uwsgi/app/pdns-admin/pdns-admin.socket;
 }

 location /pdns/static/ {
     alias /opt/pdns-admin/PowerDNS-Admin/app/static/;
 }
 ```
3. Restart nginx and uwsgi.
4. You're done and PowerDNS-Admin will now be available via nginx.