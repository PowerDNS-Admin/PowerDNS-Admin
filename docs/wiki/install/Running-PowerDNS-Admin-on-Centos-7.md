```
NOTE: If you are logged in as User and not root, add "sudo", or get root by sudo -i.
```
<br>

**Remove old Python 3.4**<br>
If you had it installed because of older instructions<br>
```
yum remove python34*
yum autoremove
```
<br>

## Install required packages
**Install needed repositories:**
<br>
```
yum install epel-release
yum install https://repo.ius.io/ius-release-el7.rpm https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
```

**Install Python 3.6 and tools**
```
yum install python3 python3-devel python3-pip
pip3.6 install -U pip
pip install -U virtualenv
```

**Install required packages for building python libraries from requirements.txt file**
```
--> NOTE: I am using MySQL Community server as the database backend.
          So `mysql-community-devel` is required. For MariaDB,
          and PostgreSQL the required package will be different.
```

If you use MariaDB ( from [MariaDB repositories](https://mariadb.com/resources/blog/installing-mariadb-10-on-centos-7-rhel-7/) )

```
yum install gcc MariaDB-devel MariaDB-shared openldap-devel xmlsec1-devel xmlsec1-openssl libtool-ltdl-devel
```

If you use default Centos mariadb (5.5)
```
yum install gcc mariadb-devel openldap-devel xmlsec1-devel xmlsec1-openssl libtool-ltdl-devel
```


**Install yarn to build asset files + Nodejs 14**
```
curl -sL https://rpm.nodesource.com/setup_14.x | bash -
curl -sL https://dl.yarnpkg.com/rpm/yarn.repo -o /etc/yum.repos.d/yarn.repo
yum install yarn
```
<br>

## Checkout source code and create virtualenv
NOTE: Please adjust `/opt/web/powerdns-admin` to your local web application directory

```
git clone https://github.com/PowerDNS-Admin/PowerDNS-Admin.git /opt/web/powerdns-admin
cd /opt/web/powerdns-admin
virtualenv -p python3 flask
```

Activate your python3 environment and install libraries:
```
. ./flask/bin/activate
pip install python-dotenv
pip install -r requirements.txt
```
<br>

## Running PowerDNS-Admin
NOTE: The default config file is located at `./powerdnsadmin/default_config.py`. If you want to load another one, please set the `FLASK_CONF` environment variable. E.g.
```bash
export FLASK_CONF=../configs/development.py
```

**Then create the database schema by running:**
```
export FLASK_APP=powerdnsadmin/__init__.py
flask db upgrade
```

**Also, we should generate asset files:**
```
yarn install --pure-lockfile
flask assets build
```

**Now you can run PowerDNS-Admin by command:**
```
./run.py
```

Open your web browser and access to `http://localhost:9191` to visit PowerDNS-Admin web interface. Register an user. The first user will be in Administrator role.

At the first time you login into the PDA UI, you will be redirected to setting page to configure the PDNS API information.

_**Note:**_ For production environment, i would recommend you to run PowerDNS-Admin with gunicorn or uwsgi instead of flask's built-in web server, take a look at WIKI page to see how to configure them.