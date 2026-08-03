# Getting Started with PowerDNS-Admin

Before you can use PowerDNS-Admin, you need to configure the database connection. This is done by setting the `SQLALCHEMY_DATABASE_URI` in your `FLASK_CONF` file. The location of this file may vary depending on your installation method.

### Database Configuration

For **MySQL / MariaDB**:

```
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@127.0.0.1/db_name'
```

For **PostgreSQL**:

```
SQLALCHEMY_DATABASE_URI = 'postgresql://powerdnsadmin:powerdnsadmin@127.0.0.1/powerdnsadmindb'
```

### First-time Login

Once you have configured the database, open your web browser and navigate to `http://localhost:9191` to access the PowerDNS-Admin web interface.

The first user to register will be granted the Administrator role.
