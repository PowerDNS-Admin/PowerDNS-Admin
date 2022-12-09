# Getting started with PowerDNS-Admin


In your `config.py` file, make sure you have the database URI filled in:

For MySQL / MariaDB:
```
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@127.0.0.1/db_name'
```

For Postgres:
```
SQLALCHEMY_DATABASE_URI = 'postgresql://powerdnsadmin:powerdnsadmin@127.0.0.1/powerdnsadmindb'
```

