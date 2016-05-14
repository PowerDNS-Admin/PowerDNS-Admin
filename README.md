# PowerDNS-Admin
PowerDNS Web-GUI - Built by Flask

#### Features:
- Multiple domain management
- Local / LDAP user authentication
- User management
- User access management base on domain
- User activity logging
- Dashboard and pdns service statistics

## Setup

### pdns Service
I assume that you have already installed powerdns service. Make sure that your `/etc/pdns/pdns.conf` has these contents
```
experimental-json-interface=yes
experimental-api-key=your-powerdns-api-key
webserver=yes
```
It will help to enable API access feature in PowerDNS so our PowerDNS-Admin can intergrate with backend services.

### Create Database
We will create a database which used by this web application. Please note that this database is difference from pdns database itself.
```
MariaDB [(none)]> CREATE DATABASE powerdnsadmin;

MariaDB [(none)]> GRANT ALL PRIVILEGES ON powerdnsadmin.* TO powerdnsadmin@'%' IDENTIFIED BY 'your-password';
```

### PowerDNS-Admin

In this installation guide, I am using CentOS 7 and run my python stuffs with *virtualenv*. If you don't have it, let install:
```
$ sudo yum install python-pip
$ sudo pip install virtualenv
```

In your python web app directory, create a `flask` directory via `virtualenv`
```
$ virtualenv flask
```

Enable virtualenv and install python 3rd libraries
```
$ source ./flask/bin/activate
(flask)$ pip install -r requirements.txt
```

Web application configuration is stored in `config.py` file. Let's clone it from `config_template.py` file and then edit it
```
(flask)$ cp config_template.py config.py 
(flask)$ vim config.py
```

Create database after having proper configs
```
(flask)% ./createdb.py
```


Run the application and enjoy!
```
(flask)$ ./run.py
```

### Screenshots
![login page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-login.png?raw=true)
![dashboard](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-dashboard.png?raw=true)
![create domain page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-domaincreate.png?raw=true)
![manage domain page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-domainmanage.png?raw=true)

