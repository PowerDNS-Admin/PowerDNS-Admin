# PowerDNS-Admin
A PowerDNS web interface with advanced features.

[![Build Status](https://travis-ci.org/ngoduykhanh/PowerDNS-Admin.svg?branch=master)](https://travis-ci.org/ngoduykhanh/PowerDNS-Admin)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/ngoduykhanh/PowerDNS-Admin.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/ngoduykhanh/PowerDNS-Admin/context:python)
[![Language grade: JavaScript](https://img.shields.io/lgtm/grade/javascript/g/ngoduykhanh/PowerDNS-Admin.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/ngoduykhanh/PowerDNS-Admin/context:javascript)

#### Features:
- Multiple domain management
- Domain template
- User management
- User access management based on domain
- User activity logging
- Support Local DB / SAML / LDAP / Active Directory user authentication
- Support Google / Github / OpenID OAuth
- Support Two-factor authentication (TOTP)
- Dashboard and pdns service statistics
- DynDNS 2 protocol support
- Edit IPv6 PTRs using IPv6 addresses directly (no more editing of literal addresses!)

### Running PowerDNS-Admin
There are several ways to run PowerDNS-Admin. Following is a simple way to start PowerDNS-Admin with docker in development environment which has PowerDNS-Admin, PowerDNS server and MySQL Back-End Database.

Step 1: Changing configuration

The configuration file for developement environment is located at `configs/development.py`, you can override some configs by editing `.env` file.

Step 2: Build docker images

```$ docker-compose build```

Step 3: Start docker containers

```$ docker-compose up```

You can now access PowerDNS-Admin at url http://localhost:9191

**NOTE:** For other methods to run PowerDNS-Admin, please take look at WIKI pages.

### Screenshots
![dashboard](https://user-images.githubusercontent.com/6447444/44068603-0d2d81f6-9fa5-11e8-83af-14e2ad79e370.png)

