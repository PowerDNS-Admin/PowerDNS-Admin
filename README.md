# PowerDNS-Admin
PowerDNS Web-GUI - Built by Flask

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

MariaDB [(none)]> GRANT ALL PRIVIELGES ON powerdnsadmin.* TO powerdnsadmin@'%' IDENTIFIED BY 'your-password';
```

### PowerDNS-Admin

In this installation guide, I am using CentOS 7 and run my pythong stuffs with *virtualenv*. If you don't have it, let install:
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

Create database after having proper configs
(flask)% ./createdb.py

Manually add some data into our `powerdnsadmin` database
```
$ mysql

MariaDB [(none)]> use powerdnsadmin;

MariaDB [powerdnsadmin]> INSERT INTO role(name, description) VALUES ('Administrator', 'Administrator');
Query OK, 1 row affected (0.00 sec)

MariaDB [powerdnsadmin]> INSERT INTO role(name, description) VALUES ('User', 'User');
Query OK, 1 row affected (0.01 sec)

MariaDB [powerdnsadmin]> INSERT INTO setting(name, value) VALUES('maintenance', 'False');
Query OK, 1 row affected (0.00 sec)
```

Run the application and enjoy!
```
(flask)$ ./run.py
```

### Screenshot
![Alt text](http://i.imgur.com/wA5qy2d.png)
