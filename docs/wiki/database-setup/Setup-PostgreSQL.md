# Setup Postgres database for PowerDNS-Admin

This guide will show you how to prepare a PostgreSQL database for PowerDNS-Admin.

We assume the database is installed per your platform's directions (apt, yum, etc). Directions to do this can be found below:

- https://www.postgresql.org/download/
- https://www.digitalocean.com/community/tutorials/how-to-install-postgresql-on-ubuntu-22-04-quickstart

We assume a default configuration and only the postgres user existing.

## Setup database
The below will create a database called powerdnsadmindb and a user of powerdnsadmin.

```
$ sudo su - postgres
$ createuser powerdnsadmin
$ createdb -E UTF8 -l en_US.UTF-8 -O powerdnsadmin -T template0 powerdnsadmindb 'The database for PowerDNS-Admin'
$ psql
postgres=# ALTER ROLE powerdnsadmin WITH PASSWORD 'powerdnsadmin_password';
```

Note:
- Please change the information above (db, user, password) to fit your setup.

### Setup Remote access to database:
If your database is on a different server postgres does not allow remote connections by default.

To change this follow the below directions:
```
[root@host ~]$  sudo su - postgres
# Edit /var/lib/pgsql/data/postgresql.conf
# Change the following line:
listen_addresses = 'localhost'
# to:
listen_addresses = '*'
# Edit /var/lib/pgsql/data/pg_hba.conf
# Add the following lines to the end of the 
host    all             all              0.0.0.0/0                       md5
host    all             all              ::/0                            md5

[postgres@host ~]$ exit
[root@host ~]$ sudo systemctl restart postgresql
```

On debian based systems these files are located in:
```
/etc/postgresql/<version>/main/
```

## Install required packages:
### Red-hat based systems:
TODO: confirm this is correct
```
sudo yum install postgresql-libs
```

### Debian based systems:
```
apt install python3-psycopg2
```

## Known Issues:

** To fill in **


## Docker (TODO: to move to docker docs)
TODO: Setup a local Docker postgres database ready to go (should probably move to the top).
```
docker run --name pdnsadmin-test -e BIND_ADDRESS=0.0.0.0 
-e SECRET_KEY='a-very-secret-key' 
-e PORT='9191' 
-e SQLA_DB_USER='powerdns_admin_user' 
-e SQLA_DB_PASSWORD='exceptionallysecure' 
-e SQLA_DB_HOST='192.168.0.100' 
-e SQLA_DB_NAME='powerdns_admin_test' 
-v /data/node_modules:/var/www/powerdns-admin/node_modules -d -p 9191:9191 ixpict/powerdns-admin-pgsql:latest
```
