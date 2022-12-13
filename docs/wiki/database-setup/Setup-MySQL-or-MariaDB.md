# Setup MySQL database for PowerDNS-Admin

This guide will show you how to prepare a MySQL or MariaDB database for PowerDNS-Admin.

We assume the database is installed per your platform's directions (apt, yum, etc). Directions to do this can be found below:
- MariaDB:
    - https://mariadb.com/kb/en/getting-installing-and-upgrading-mariadb/
    - https://www.digitalocean.com/community/tutorials/how-to-install-mariadb-on-ubuntu-20-04
- MySQL:
    - https://dev.mysql.com/downloads/mysql/
    - https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-20-04

The following directions assume a default configuration and for productions setups `mysql_secure_installation` has been run.

## Setup database:

Connect to the database (Usually using `mysql -u root -p` if a password has been set on the root database user or `sudo mysql` if not), then enter the following:
```
CREATE DATABASE `powerdnsadmin` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON `powerdnsadmin`.* TO 'pdnsadminuser'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD_HERE';
FLUSH PRIVILEGES;
```
- If your database server is located on a different machine then change 'localhost' to '%'
- Replace YOUR_PASSWORD_HERE with a secure password.

Once there are no errors you can type `quit` in the mysql shell to exit from it.

## Install required packages:
### Red-hat based systems:
```
yum install MariaDB-shared mariadb-devel mysql-community-devel
```

### Debian based systems:
```
apt install libmysqlclient-dev
```

### Install python packages:
```
pip3 install mysqlclient==2.0.1
```

## Known issues:

Problem: If you plan to manage large zones, you may encounter some issues while applying changes. This is due to PowerDNS-Admin trying to insert the entire modified zone into the column history.detail.

Using MySQL/MariaDB, this column is created by default as TEXT and thus limited to 65,535 characters.

Solution: Convert the column to MEDIUMTEXT:
1. Connect to the database shell as described in the setup database section:
2. Execute the following commands:
    ```
    USE powerdnsadmin;
    ALTER TABLE history MODIFY detail MEDIUMTEXT;
    ```
