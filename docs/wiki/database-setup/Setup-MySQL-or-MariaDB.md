# Setup MySQL database for PowerDNS-Admin

This guide will show you how to prepare a MySQL or MariaDB database for PowerDNS-Admin.

We assume the database is installed per your platform's directions (apt, yum, etc).

## Setup database:

Connect to the database (Usually using `mysql -u root -p` - then enter your MySQL/MariaDB root users password if applicable), then enter the following:
```
CREATE DATABASE `powerdnsadmin` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON `powerdnsadmin`.* TO 'pdnsadminuser'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD_HERE';
FLUSH PRIVILEGES;
quit
```

## Known issues:

Problem: If you plan to manage large zones, you may encounter some issues while applying changes. This is due to PowerDNS-Admin trying to insert the entire modified zone into the column history.detail.

Using MySQL/MariaDB, this column is created by default as TEXT and thus limited to 65,535 characters.

Solution: Convert the column to MEDIUMTEXT:
```
USE powerdnsadmin;
ALTER TABLE history MODIFY detail MEDIUMTEXT;
```
