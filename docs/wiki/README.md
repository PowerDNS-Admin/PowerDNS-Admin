# PowerDNS-Admin wiki

## Database Setup guides

- [MySQL / MariaDB](database-setup/Setup-MySQL-or-MariaDB.md)
- [PostgreSQL](database-setup/Setup-PostgreSQL.md)

## Installation guides

- [General (Read this first)](install/General.md)
  - BSD:
    - [Install on FreeBSD 12.1-RELEASE](install/Running-on-FreeBSD.md)
  - Containers:
    - [Install on Docker](install/Running-PowerDNS-Admin-on-Docker.md)
  - Debian:
    - [Install on Ubuntu or Debian](install/Running-PowerDNS-Admin-on-Ubuntu-or-Debian.md)
  - Red-Hat:
    - [Install on Centos 7](install/Running-PowerDNS-Admin-on-Centos-7.md)
    - [Install on Fedora 23](install/Running-PowerDNS-Admin-on-Fedora-23.md)
    - [Install on Fedora 30](install/Running-PowerDNS-Admin-on-Fedora-30.md)

### Post install Setup

- [Environment Variables](configuration/Environment-variables.md)
- [Getting started](configuration/Getting-started.md)
- SystemD:
  - [Running PowerDNS-Admin as a service using Systemd](install/Running-PowerDNS-Admin-as-a-service-(Systemd).md)

### Web Server configuration

- [Supervisord](web-server/Supervisord-example.md)
- [Systemd](web-server/Systemd-example.md)
- [Systemd + Gunicorn + Nginx](web-server/Running-PowerDNS-Admin-with-Systemd-Gunicorn-and-Nginx.md)
- [Systemd + Gunicorn + Apache](web-server/Running-PowerDNS-Admin-with-Systemd,-Gunicorn-and-Apache.md)
- [uWSGI](web-server/uWSGI-example.md)
- [WSGI-Apache](web-server/WSGI-Apache-example.md)
- [Docker-ApacheReverseProxy](web-server/Running-Docker-Apache-Reverseproxy.md)

## Using PowerDNS-Admin

- Setting up a zone
- Adding a record

## Feature usage

- [DynDNS2](features/DynDNS2.md)

## Debugging

- [Debugging the build process](debug/build-process.md)
