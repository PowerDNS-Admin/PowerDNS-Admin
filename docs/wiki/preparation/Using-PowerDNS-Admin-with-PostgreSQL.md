If you would like to use PostgreSQL instead of MySQL or MariaDB, you have to install difference dependencies. Check the following instructions.

### Install dependencies
```
$ sudo yum install postgresql-libs
$ pip install psycopg2
```

### Create database
```
$ sudo su - postgres
$ createuser powerdnsadmin
$ createdb powerdnsadmindb
$ psql
postgres=# alter user powerdnsadmin with encrypted password 'powerdnsadmin';
postgres=# grant all privileges on database powerdnsadmindb to powerdnsadmin;
```

In your `config.py` file, make sure you have
```
SQLALCHEMY_DATABASE_URI = 'postgresql://powerdnsadmin:powerdnsadmin@127.0.0.1/powerdnsadmindb'
```

Note:
- Please change the information above (db, user, password) to fit your setup.
- You might need to adjust your PostgreSQL's `pg_hba.conf` config file to allow password authentication for networks.

### Use Docker
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