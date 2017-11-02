# PowerDNS-Admin
PowerDNS Web-GUI - Built by Flask
[![Build Status](https://travis-ci.org/thomasDOTde/PowerDNS-Admin.svg?branch=master)](https://travis-ci.org/thomasDOTde/PowerDNS-Admin)

#### Features:
- Multiple domain management
- Local / LDAP user authentication
- Support Two-factor authentication (TOTP)
- Support SAML authentication
- Google oauth authentication
- Github oauth authentication
- User management
- User access management based on domain
- User activity logging
- Dashboard and pdns service statistics
- DynDNS 2 protocol support
- Edit IPv6 PTRs using IPv6 addresses directly (no more editing of literal addresses!)

## Setup

### PowerDNS Version Support:
PowerDNS-Admin supports PowerDNS autoritative server versions **3.4.2** and higher. 

### pdns Service
I assume that you have already installed powerdns service. Make sure that your `/etc/pdns/pdns.conf` has these contents

PowerDNS 4.0.0 and later
```
api=yes
api-key=your-powerdns-api-key
webserver=yes
```

PowerDNS before 4.0.0
```
experimental-json-interface=yes
experimental-api-key=your-powerdns-api-key
webserver=yes
```

This will enable API access in PowerDNS so PowerDNS-Admin can intergrate with PowerDNS.

### Create Database
We will create a database which used by this web application. Please note that this database is difference from pdns database itself.

You could use any database that SQLAlchemy supports. For example MySQL (you will need to `pip install MySQL-python` to use MySQL backend):
```
MariaDB [(none)]> CREATE DATABASE powerdnsadmin;

MariaDB [(none)]> GRANT ALL PRIVILEGES ON powerdnsadmin.* TO powerdnsadmin@'%' IDENTIFIED BY 'your-password';
```
For testing purpose, you could also use SQLite as backend. This way you do not have to install `MySQL-python` dependency.


### PowerDNS-Admin

In this installation guide, I am using CentOS 7 and run my python stuffs with *virtualenv*. If you don't have it, lets install it:
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

You can configure group based security by tweaking the below parameters in `config.py`. Groups membership comes from LDAP.
Setting `LDAP_GROUP_SECURITY` to True enables group-based security. With this enabled only members of the two groups listed below are allowed to login. Members of `LDAP_ADMIN_GROUP` will get the Administrator role and members of `LDAP_USER_GROUP` will get the User role. Sample config below:
```
LDAP_GROUP_SECURITY = True
LDAP_ADMIN_GROUP = 'CN=PowerDNS-Admin Admin,OU=Custom,DC=ivan,DC=local'
LDAP_USER_GROUP = 'CN=PowerDNS-Admin User,OU=Custom,DC=ivan,DC=local'
```

Create database after having proper configs
```
(flask)% ./create_db.py
```


Run the application and enjoy!
```
(flask)$ ./run.py
```

### SAML Authentication
SAML authentication is supported. Setting are retrieved from Metdata-XML.
Metadata URL is configured in config.py as well as caching interval.
Following Assertions are supported and used by this application:
- nameidentifier in form of email address as user login
- email used as user email address
- givenname used as firstname
- surname used as lastname

### ADFS claim rules as example
Microsoft Active Directory Federation Services can be used as Identity Provider for SAML login.
The Following rules should be configured to send all attribute information to PowerDNS-Admin.
The nameidentifier should be something stable from the idp side. All other attributes are update when singing in.

#### sending the nameidentifier
Name-Identifiers Type is "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
```
c:[Type == "<here goes your source claim>"]
 => issue(Type = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier", Issuer = c.Issuer, OriginalIssuer = c.OriginalIssuer, Value = c.Value, ValueType = c.ValueType, Properties["http://schemas.xmlsoap.org/ws/2005/05/identity/claimproperties/format"] = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress");
```

#### sending the firstname
Name-Identifiers Type is "givenname"
```
c:[Type == "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"]
 => issue(Type = "givenname", Issuer = c.Issuer, OriginalIssuer = c.OriginalIssuer, Value = c.Value, ValueType = c.ValueType, Properties["http://schemas.xmlsoap.org/ws/2005/05/identity/claimproperties/format"] = "urn:oasis:names:tc:SAML:1.1:nameid-format:transient");
```

#### sending the lastname
Name-Identifiers Type is "surname"
```
c:[Type == "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"]
 => issue(Type = "surname", Issuer = c.Issuer, OriginalIssuer = c.OriginalIssuer, Value = c.Value, ValueType = c.ValueType, Properties["http://schemas.xmlsoap.org/ws/2005/05/identity/claimproperties/format"] = "urn:oasis:names:tc:SAML:1.1:nameid-format:transient");
```

#### sending the email
Name-Identifiers Type is "email"
```
c:[Type == "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"]
 => issue(Type = "email", Issuer = c.Issuer, OriginalIssuer = c.OriginalIssuer, Value = c.Value, ValueType = c.ValueType, Properties["http://schemas.xmlsoap.org/ws/2005/05/identity/claimproperties/format"] = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress");
```

### Screenshots
![login page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-login.png?raw=true)
![dashboard](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-dashboard.png?raw=true)
![create domain page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-domaincreate.png?raw=true)
![manage domain page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-domainmanage.png?raw=true)
![two-factor authentication config](https://cloud.githubusercontent.com/assets/6447444/16111111/467f2226-33db-11e6-926a-01b4d15035d2.png)

