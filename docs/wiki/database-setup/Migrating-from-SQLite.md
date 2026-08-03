> **Disclaimer:** This guide provides general guidance and is based on a best-effort approach. It is not a substitute for the official documentation of your chosen database system. We strongly recommend that you consult the official documentation for both your source and target databases before proceeding with the migration.

# Migrating from SQLite to MySQL or PostgreSQL

This guide provides instructions for migrating your PowerDNS-Admin database from SQLite to a new MySQL or PostgreSQL database on a remote host. This is often necessary when scaling up your installation or when you require the advanced features of a more robust database system.

**It is critical that you back up your data before you begin.**

## Prerequisites

Before you start the migration, please ensure you have the following:

-   Shell access to the server where your PowerDNS-Admin instance is running.
-   The path to your existing SQLite database file (e.g., `/path/to/your/powerdns.db`).
-   Administrative access to your new remote MySQL or PostgreSQL database server.
-   Network access from your PowerDNS-Admin server to your remote database server.

---

## Migration to MySQL (Recommended)

Migrating to MySQL is the recommended approach.

### Step 1: Stop PowerDNS-Admin

Ensure that your PowerDNS-Admin application is not running.

### Step 2: Back Up Your SQLite Database

Create a backup of your SQLite database file:

```console
cp /path/to/your/powerdns.db /path/to/your/powerdns.db.backup
```

### Step 3: Install a Conversion Tool

We recommend using a tool to convert the SQLite database to a MySQL-compatible format. `sqlite3-to-mysql` is a popular Python utility for this purpose.

```console
pip install sqlite3-to-mysql
```

### Step 4: Prepare the Remote MySQL Database

On your remote database server, create a new database and user for PowerDNS-Admin. Grant the new user the necessary permissions to access the database from your PowerDNS-Admin server's IP address.

```sql
CREATE DATABASE powerdnsadmin;
CREATE USER 'pdnsadmin'@'your-powerdns-admin-server-ip' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON powerdnsadmin.* TO 'pdnsadmin'@'your-powerdns-admin-server-ip';
FLUSH PRIVILEGES;
```

### Step 5: Convert and Import the Data

Use the `sqlite3-to-mysql` tool to transfer the data. Provide the path to your SQLite file and the connection details for your remote MySQL database.

```console
sqlite3mysql -f /path/to/your/powerdns.db -d powerdnsadmin -h your-mysql-host -u pdnsadmin -p
```

The tool will prompt you for your MySQL password.

### Step 6: Update PowerDNS-Admin Configuration

Update the `SQLALCHEMY_DATABASE_URI` in your PowerDNS-Admin configuration to point to your new remote MySQL database:

```
SQLALCHEMY_DATABASE_URI = 'mysql://pdnsadmin:your-password@your-mysql-host/powerdnsadmin'
```

### Step 7: Start and Verify

Start your PowerDNS-Admin application. It will now be connected to the remote MySQL database. Log in and verify that all of your data has been migrated correctly.

---

## Migration to PostgreSQL

Migrating to PostgreSQL is also a viable option. The process can be automated with tools like `pgloader`.

### Step 1: Stop PowerDNS-Admin

Ensure that your PowerDNS-Admin application is not running to prevent any data changes during the migration.

### Step 2: Back Up Your SQLite Database

Create a backup of your SQLite database file:

```console
cp /path/to/your/powerdns.db /path/to/your/powerdns.db.backup
```

### Step 3: Install pgloader

Install `pgloader` on your PowerDNS-Admin server using your system's package manager.

For Debian/Ubuntu:
```console
sudo apt-get update
sudo apt-get install pgloader
```

For CentOS/RHEL:
```console
sudo yum install pgloader
```

### Step 4: Prepare the Remote PostgreSQL Database

On your remote database server, create a new database and user for PowerDNS-Admin.

```sql
CREATE DATABASE powerdnsadmin;
CREATE USER pdnsadmin WITH ENCRYPTED PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE powerdnsadmin TO pdnsadmin;
```

You will also need to configure PostgreSQL to accept remote connections. Edit the `pg_hba.conf` file to add a new entry for your PowerDNS-Admin server's IP address.

### Step 5: Run pgloader

Run `pgloader` to migrate the data from your SQLite database to your new remote PostgreSQL database. Replace the file path and connection string with your own values.

```console
pgloader /path/to/your/powerdns.db "postgresql://pdnsadmin:your-password@your-postgres-host/powerdnsadmin"
```

`pgloader` will automatically handle schema creation, data type conversion, and data transfer.

### Step 6: Update PowerDNS-Admin Configuration

Update the `SQLALCHEMY_DATABASE_URI` in your PowerDNS-Admin configuration to point to your new remote PostgreSQL database:

```
SQLALCHEMY_DATABASE_URI = 'postgresql://pdnsadmin:your-password@your-postgres-host/powerdnsadmin'
```

### Step 7: Start and Verify

Start your PowerDNS-Admin application. It will now be connected to the remote PostgreSQL database. Log in and verify that all of your data has been migrated correctly.
