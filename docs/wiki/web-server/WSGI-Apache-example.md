How to run PowerDNS-Admin via WSGI and Apache2.4 using mod_wsgi.

**Note**: You must install mod_wsgi by using pip3 instead of system default mod_wsgi!!!

### Ubuntu/Debian
```shell
# apt install apache2-dev
# virtualenv -p python3 flask
# source ./flask/bin/activate
(flask) # pip3 install mod-wsgi
(flask) # mod_wsgi-express install-module > /etc/apache2/mods-available/wsgi.load
(flask) # a2enmod wsgi
(flask) # systemctl restart apache2
```
### CentOS
```shell
# yum install httpd-devel
# virtualenv -p python3 flask
# source ./flask/bin/activate
(flask) # pip3 install mod-wsgi
(flask) # mod_wsgi-express install-module > /etc/httpd/conf.modules.d/02-wsgi.conf
(flask) # systemctl restart httpd
```
### Fedora
```bash
# Install Apache's Development interfaces and package requirements
dnf install httpd-devel gcc gc make
virtualenv -p python3 flask
source ./flask/bin/activate
# Install WSGI for HTTPD
pip install mod_wsgi-httpd
# Install WSGI
pip install mod-wsgi
# Enable the module in Apache:
mod_wsgi-express install-module > /etc/httpd/conf.modules.d/02-wsgi.conf
systemctl restart httpd
```

Apache vhost configuration;
```apache
<VirtualHost *:443>
        ServerName superawesomedns.foo.bar
        ServerAlias [fe80::1]
        ServerAdmin webmaster@foo.bar

        SSLEngine On
        SSLCertificateFile /some/path/ssl/certs/cert.pem
        SSLCertificateKeyFile /some/path/ssl/private/cert.key

        ErrorLog /var/log/apache2/error-superawesomedns.foo.bar.log
        CustomLog /var/log/apache2/access-superawesomedns.foo.bar.log combined

        DocumentRoot /srv/vhosts/superawesomedns.foo.bar/

        WSGIDaemonProcess pdnsadmin user=pdnsadmin group=pdnsadmin threads=5
        WSGIScriptAlias / /srv/vhosts/superawesomedns.foo.bar/powerdnsadmin.wsgi

        # pass BasicAuth on to the WSGI process
        WSGIPassAuthorization On

        <Directory "/srv/vhosts/superawesomedns.foo.bar/">
                WSGIProcessGroup pdnsadmin
                WSGIApplicationGroup %{GLOBAL}

                AllowOverride None
                Options +ExecCGI +FollowSymLinks
                SSLRequireSSL
                AllowOverride None
                Require all granted
        </Directory>
</VirtualHost>
```
**In Fedora, you might want to change the following line:**
```apache
WSGIDaemonProcess pdnsadmin socket-user=apache user=pdnsadmin group=pdnsadmin threads=5
```
**And you should add the following line to `/etc/httpd/conf/httpd.conf`:**
```apache
WSGISocketPrefix /var/run/wsgi
```

Content of `/srv/vhosts/superawesomedns.foo.bar/powerdnsadmin.wsgi`;
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/srv/vhosts/superawesomedns.foo.bar')

from app import app as application
```
Starting from 0.2 version, the `powerdnsadmin.wsgi` file is slighty different : 
```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/srv/vhosts/superawesomedns.foo.bar')

from powerdnsadmin import create_app
application = create_app()
```

(this implies that the pdnsadmin user/group exists, and that you have mod_wsgi loaded)