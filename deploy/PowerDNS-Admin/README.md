# PowerDNS-Admin
A PowerDNS web interface with advanced features.

[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/PowerDNS-Admin/PowerDNS-Admin.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/PowerDNS-Admin/PowerDNS-Admin/context:python)
[![Language grade: JavaScript](https://img.shields.io/lgtm/grade/javascript/g/PowerDNS-Admin/PowerDNS-Admin.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/PowerDNS-Admin/PowerDNS-Admin/context:javascript)

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
If you are looking to install and run PowerDNS-Admin directly onto your system check out the [Wiki](https://github.com/PowerDNS-Admin/PowerDNS-Admin/wiki#installation-guides) for ways to do that.

### Docker
These are two options to run PowerDNS-Admin using Docker.
To get started as quickly as possible try option 1. If you want to make modifications to the configuration option 2 may be cleaner.

#### Option 1: From Docker Hub
The easiest is to just run the latest Docker image from Docker Hub:
```
$ docker run -d \
    -e SECRET_KEY='a-very-secret-key' \
    -v pda-data:/data \
    -p 9191:80 \
    ngoduykhanh/powerdns-admin:latest
```
This creates a volume called `pda-data` to persist the SQLite database with the configuration.

#### Option 2: Using docker-compose
1. Update the configuration   
   Edit the `docker-compose.yml` file to update the database connection string in `SQLALCHEMY_DATABASE_URI`.
   Other environment variables are mentioned in the [legal_envvars](https://github.com/PowerDNS-Admin/PowerDNS-Admin/blob/master/configs/docker_config.py#L5-L46).
   To use the Docker secrets feature it is possible to append `_FILE` to the environment variables and point to a file with the values stored in it.   
   Make sure to set the environment variable `SECRET_KEY` to a long random string (https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY)

2. Start docker container
   ```
   $ docker-compose up
   ```

You can then access PowerDNS-Admin by pointing your browser to http://localhost:9191.

### Kubernetes
There are three options to run PowerDNS-Admin in a kubernetes cluster. This currently assumes you already have an existing MySQL server setup and ready for use for powerdns-admin. This chart also supports Rancher chart questions, so that when installing in rancher you have a nice UI to enter all the parameters. You must package and push the chart to your own chart repository to use in rancher.

#### Option 1: Using helm chart with github repo
1. Register github repo with helm.  
   `helm repo add powerdns-admin https://raw.githubusercontent.com/johnwc/PowerDNS-Admin/master/deploy/`
2. Create and customize personalized installation settings file `myvalues.yaml`. Use existing [values.yaml](https://github.com/johnwc/PowerDNS-Admin/blob/master/deploy/PowerDNS-Admin/values.yaml) as template.
3. Install powerdns-admin  
   `helm install -n power-dns -f myvalues.yaml <install_name> powerdns-admin`

#### Option 2: Using helm chart local install
1. Clone the existing github repo to your local machine.  
   `git clone https://github.com/johnwc/PowerDNS-Admin`
2. Change directory into `./PowerDNS-Admin/deploy`
3. Install powerdns-admin  
   `helm install -n power-dns -f myvalues.yaml <install_name> ./PowerDNS-Admin/`

The notes output from the install will explain how to access PowerDNS-Admin. If you enable ingress and/or cert-manager it can be something like http://powerdns-admin.mydomain.com or https://powerdns-admin.mydomain.com, whatever hostname you set in `myvalues.yaml`.

## Screenshots
![dashboard](https://user-images.githubusercontent.com/6447444/44068603-0d2d81f6-9fa5-11e8-83af-14e2ad79e370.png)

## LICENSE
MIT. See [LICENSE](https://github.com/PowerDNS-Admin/PowerDNS-Admin/blob/master/LICENSE)

