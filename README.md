# PowerDNS-Admin
A PowerDNS web interface with advanced features.
[![Build Status](https://travis-ci.org/ngoduykhanh/PowerDNS-Admin.svg?branch=master)](https://travis-ci.org/ngoduykhanh/PowerDNS-Admin)

#### Features:
- Multiple domain management
- Domain template
- User management
- User access management based on domain
- User activity logging
- Local DB / LDAP / Active Directory user authentication
- Support SAML authentication
- Google oauth authentication
- Github oauth authentication
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
![login page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-login.png?raw=true)
![dashboard](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-dashboard.png?raw=true)
![create domain page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-domaincreate.png?raw=true)
![manage domain page](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/images/readme_screenshots/fullscreen-domainmanage.png?raw=true)
![two-factor authentication config](https://cloud.githubusercontent.com/assets/6447444/16111111/467f2226-33db-11e6-926a-01b4d15035d2.png)

