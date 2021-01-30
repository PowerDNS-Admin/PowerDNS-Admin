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
- Support Google / Github / Azure / OpenID OAuth
- Support Two-factor authentication (TOTP)
- Dashboard and pdns service statistics
- DynDNS 2 protocol support
- Edit IPv6 PTRs using IPv6 addresses directly (no more editing of literal addresses!)
- Limited API for manipulating zones and records
- Full IDN/Punycode support

## Running PowerDNS-Admin
There are several ways to run PowerDNS-Admin. The easiest way is to use Docker.
If you are looking to install and run PowerDNS-Admin directly onto your system check out the [Wiki](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki#installation-guides) for ways to do that.

### Docker
This are two options to run PowerDNS-Admin using Docker.
To get started as quickly as possible try option 1. If you want to make modifications to the configuration option 2 may be cleaner.

#### Option 1: From Docker Hub
The easiest is to just run the latest Docker image from Docker Hub:
```
$ docker run -d \
    -v pda-data:/data \
    -p 9191:80 \
    ngoduykhanh/powerdns-admin:latest
```
This creates a volume called `pda-data` to persist the SQLite database with the configuration.

#### Option 2: Using docker-compose
1. Update the configuration
   Edit the `docker-compose.yml` file to update the database connection string in `SQLALCHEMY_DATABASE_URI`.
   Other environment variables are mentioned in the [legal_envvars](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/configs/docker_config.py#L5-L46).
   To use the Docker secrets feature it is possible to append `_FILE` to the environment variables and point to a file with the values stored in it.

2. Start docker container
   ```
   $ docker-compose up
   ```

You can then access PowerDNS-Admin by pointing your browser to http://localhost:9191.

## Screenshots
![dashboard](https://user-images.githubusercontent.com/6447444/44068603-0d2d81f6-9fa5-11e8-83af-14e2ad79e370.png)

## LICENSE
MIT. See [LICENSE](https://github.com/ngoduykhanh/PowerDNS-Admin/blob/master/LICENSE)

## Support
If you like the project and want to support it, you can *buy me a coffee* ☕

<a href="https://www.buymeacoffee.com/khanhngo" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
