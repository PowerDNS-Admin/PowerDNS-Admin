On [FreeBSD](https://www.freebsd.org/), most software is installed using `pkg`. You can always build from source with the Ports system. This method uses as many binary ports as possible, and builds some python packages from source. It installs all the required runtimes in the global system (e.g., python, node, yarn) and then builds a virtual python environment in `/opt/python`. Likewise, it installs powerdns-admin in `/opt/powerdns-admin`.

### Build an area to host files

```bash
mkdir -p /opt/python
```

### Install prerequisite runtimes: python, node, yarn

```bash
sudo pkg install git python3 curl node12 yarn-node12
sudo pkg install libxml2 libxslt pkgconf py37-xmlsec py37-cffi py37-ldap
```

## Check Out Source Code
_**Note:**_ Please adjust `/opt/powerdns-admin` to your local web application directory

```bash
git clone https://github.com/PowerDNS-Admin/PowerDNS-Admin.git /opt/powerdns-admin
cd /opt/powerdns-admin
```

## Make Virtual Python Environment

Make a virtual environment for python. Activate your python3 environment and install libraries. It's easier to install some python libraries as system packages, so we add the `--system-site-packages` option to pull those in.

> Note: I couldn't get `python-ldap` to install correctly, and I don't need it. I commented out the `python-ldap` line in `requirements.txt` and it all built and installed correctly. If you don't intend to use LDAP authentication, you'll be fine. If you need LDAP authentication, it probably won't work.

```bash
python3 -m venv /web/python --system-site-packages
source /web/python/bin/activate
/web/python/bin/python3 -m pip install --upgrade pip wheel
# this command comments out python-ldap
perl -pi -e 's,^python-ldap,\# python-ldap,' requirements.txt 
pip3 install -r requirements.txt
```

## Configuring PowerDNS-Admin

NOTE: The default config file is located at `./powerdnsadmin/default_config.py`. If you want to load another one, please set the `FLASK_CONF` environment variable. E.g.
```bash
cp configs/development.py /opt/powerdns-admin/production.py
export FLASK_CONF=/opt/powerdns-admin/production.py
```

### Update the Flask config

Edit your flask python configuration. Insert values for the database server, user name, password, etc.

```bash
vim $FLASK_CONF
```

Edit the values below to something sensible
```python
### BASIC APP CONFIG
SALT = '[something]'
SECRET_KEY = '[something]'
BIND_ADDRESS = '0.0.0.0'
PORT = 9191
OFFLINE_MODE = False

### DATABASE CONFIG
SQLA_DB_USER = 'pda'
SQLA_DB_PASSWORD = 'changeme'
SQLA_DB_HOST = '127.0.0.1'
SQLA_DB_NAME = 'pda'
SQLALCHEMY_TRACK_MODIFICATIONS = True
```

Be sure to uncomment one of the lines like `SQLALCHEMY_DATABASE_URI`.

### Initialise the database

```bash
export FLASK_APP=powerdnsadmin/__init__.py
flask db upgrade
```

### Build web assets

```bash
yarn install --pure-lockfile
flask assets build
```

## Running PowerDNS-Admin

Now you can run PowerDNS-Admin by command

```bash
./run.py
```

Open your web browser and go to `http://localhost:9191` to visit PowerDNS-Admin web interface. Register a user. The first user will be in the Administrator role.

### Running at startup

This is good for testing, but for production usage, you should use gunicorn or uwsgi. See [Running PowerDNS Admin with Systemd, Gunicorn and Nginx](../web-server/Running-PowerDNS-Admin-with-Systemd,-Gunicorn--and--Nginx.md) for instructions.

The right approach long-term is to create a startup script in `/usr/local/etc/rc.d` and enable it through `/etc/rc.conf`.