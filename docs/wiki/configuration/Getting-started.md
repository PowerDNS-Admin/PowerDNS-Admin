# Getting Started with PowerDNS-Admin

Before you can use PowerDNS-Admin, you must configure the database connection; there is no default database URI. Set `SQLALCHEMY_DATABASE_URI` in your `FLASK_CONF` file or environment, or use the split `DATABASE_*` environment variables described below. The location of `FLASK_CONF` may vary depending on your installation method.

### Database Configuration

For **MySQL / MariaDB**:

```
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@127.0.0.1/db_name'
```

For **PostgreSQL**:

```
SQLALCHEMY_DATABASE_URI = 'postgresql://powerdnsadmin:powerdnsadmin@127.0.0.1/powerdnsadmindb'
```

In Docker, you can also pass the same values as separate environment variables and let PowerDNS-Admin build the URI (user and password are percent-encoded automatically):

```
DATABASE_DRIVER=mysql
DATABASE_USER=pdnsadmin
DATABASE_PASSWORD=your-password
DATABASE_HOST=mysql
DATABASE_NAME=powerdnsadmin
DATABASE_EXTRA_PARAMS=ssl=true
```

`SQLALCHEMY_DATABASE_URI` still wins if both styles are set. See [Environment variables](Environment-variables.md) for the full list.

### First-time Login

Once you have configured the database, open your web browser and navigate to `http://localhost:9191` to access the PowerDNS-Admin web interface.

The first user to register will be granted the Administrator role.
