# Getting started with PowerDNS-Admin


In your FLASK_CONF (check the installation directions for where yours is) file, make sure you have the database URI filled in (in some previous documentation this was called config.py):

TODO: list location of config.py

For MySQL / MariaDB:
```
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@127.0.0.1/db_name'
```

For Postgres:
```
SQLALCHEMY_DATABASE_URI = 'postgresql://powerdnsadmin:powerdnsadmin@127.0.0.1/powerdnsadmindb'
```

