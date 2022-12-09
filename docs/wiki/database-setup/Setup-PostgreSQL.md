# Setup Postgres database for PowerDNS-Admin

We assume you already have a postgres database software installed for your platform.

### Create database
```
$ sudo su - postgres
$ createuser powerdnsadmin
$ createdb powerdnsadmindb
$ psql
postgres=# alter user powerdnsadmin with encrypted password 'powerdnsadmin';
postgres=# grant all privileges on database powerdnsadmindb to powerdnsadmin;
```

Note:
- Please change the information above (db, user, password) to fit your setup.

### Setup Remote access to database:
If your database is on a different server postgres does not allow remote connections by default.

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
[root@host ~]$  sudo systemctl restart postgresql
```

On debian based systems these files are located in:
```
/etc/postgresql/<version>/main/
```

## Docker
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