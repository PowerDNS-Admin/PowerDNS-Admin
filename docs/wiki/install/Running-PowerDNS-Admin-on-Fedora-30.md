**Legacy.** This guide is no longer updated. A new Fedora installation document will replace it.

```
NOTE: If you are logged in as User and not root, add "sudo", or get root by sudo -i.
      Normally under centos you are anyway mostly root.
```
<br>

## Install required packages

**Install Python and requirements**
```bash
dnf install python37 python3-devel python3-pip
```
**Install Backend and Environment prerequisites**
```bash
dnf install mariadb-devel mariadb-common openldap-devel xmlsec1-devel xmlsec1-openssl libtool-ltdl-devel
```
**Install Development tools**
```bash
dnf install gcc gc make
```
**Install PIP**
```bash
pip3.7 install -U pip
```
**Install Virtual Environment**
```bash
pip install -U virtualenv
```
**Install Yarn for building NodeJS asset files:**
```bash
dnf install npm
npm install yarn -g
```

## Clone the PowerDNS-Admin repository to the installation path:
```bash
cd /opt/web/
git clone https://github.com/PowerDNS-Admin/PowerDNS-Admin.git powerdns-admin
```

**Prepare the Virtual Environment:**
```bash
cd /opt/web/powerdns-admin
virtualenv -p python3 flask
```
**Activate the Python Environment and install libraries**
```bash
. ./flask/bin/activate
pip install python-dotenv
pip install -r requirements.txt
```

## Running PowerDNS-Admin

NOTE: The default config file is located at `./powerdnsadmin/default_config.py`. Copy `configs/development.py` and replace `SECRET_KEY` and `SALT` in the copy before starting. Startup refuses a missing, short, or published value. `SECRET_KEY` must be at least 32 characters (`python3 -c 'import secrets; print(secrets.token_hex(32))'`). `SALT` must be the output of `bcrypt.gensalt()` (`python3 -c 'import bcrypt; print(bcrypt.gensalt().decode())'`). Point `FLASK_CONF` at the copy. E.g.
```bash
cp configs/development.py configs/production.py
export FLASK_CONF=../configs/production.py
```

**Then create the database schema by running:**
```
(flask) [khanh@localhost powerdns-admin] export FLASK_APP=powerdnsadmin/__init__.py
(flask) [khanh@localhost powerdns-admin] flask db upgrade
```

**Also, we should generate asset files:**
```
(flask) [khanh@localhost powerdns-admin] yarn install --pure-lockfile
(flask) [khanh@localhost powerdns-admin] flask assets build
```

**Now you can run PowerDNS-Admin by command:**
```
(flask) [khanh@localhost powerdns-admin] ./run.py
```

Open your web browser and access to `http://localhost:9191` to visit PowerDNS-Admin web interface. Register an user. The first user will be in Administrator role.

At the first time you login into the PDA UI, you will be redirected to setting page to configure the PDNS API information.

_**Note:**_ For production environment, i recommend to run PowerDNS-Admin with WSGI over Apache instead of flask's built-in web server...  
 Take a look at [WSGI Apache Example](web-server/WSGI-Apache-example#fedora) WIKI page to see how to configure it.