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
(flask)$ copy config_template.py config.py 
(flask)$ vim config.py
```

You can configure group based security by tweaking the below parameters in `config.py`. Groups membership comes from LDAP.
Setting `LDAP_GROUP_SECURITY` to True enables group-based security. With this enabled only members of the two groups listed below are allowed to login. Members of `LDAP_ADMIN_GROUP` will get the Administrator role and members of `LDAP_USER_GROUP` will get the User role. Sample config below:
```
LDAP_GROUP_SECURITY = True
LDAP_ADMIN_GROUP = 'CN=PowerDNS-Admin Admin,OU=Custom,DC=ivan,DC=local'
LDAP_USER_GROUP = 'CN=PowerDNS-Admin User,OU=Custom,DC=ivan,DC=local'
```

Create database after having proper configs
```
(flask)% ./createdb.py
```


Run the application and enjoy!
```
(flask)$ ./run.py
```

### Screenshot
![Alt text](http://i.imgur.com/wA5qy2d.png)
