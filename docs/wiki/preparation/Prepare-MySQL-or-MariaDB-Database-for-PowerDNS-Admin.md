This guide will show you how to prepare a MySQL or MariaDB database for PowerDNS-Admin.

### Step-by-step instructions
1. ivan@ubuntu:~$ `mysql -u root -p` (then enter your MySQL/MariaDB root users password)
2. mysql> `CREATE DATABASE powerdnsadmin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
3. mysql> `GRANT ALL PRIVILEGES ON powerdnsadmin.* TO 'pdnsadminuser'@'%' IDENTIFIED BY 'p4ssw0rd';`
4. mysql> `FLUSH PRIVILEGES;`
5. mysql> `quit`

**NOTE:**

If you plan to manage large zones, you may encounter some issues while applying changes.
This is due to PowerDNS-Admin trying to insert the entire modified zone into the column history.detail.

Using MySQL/MariaDB, this column is created by default as TEXT and thus limited to 65,535 characters.

_Solution_:

Convert the column to MEDIUMTEXT: 

* `USE powerdnsadmin;`
* `ALTER TABLE history MODIFY detail MEDIUMTEXT;`