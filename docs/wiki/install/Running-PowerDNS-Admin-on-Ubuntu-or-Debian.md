# Installing PowerDNS-Admin on Ubuntu or Debian based systems

First setup your database accordingly:
[Database Setup](../database-setup/README.md)

## Install required packages:

### Install required packages for building python libraries from requirements.txt file

For Debian 11 (bullseye) and above:
```bash
sudo apt install -y python3-dev git libsasl2-dev libldap2-dev python3-venv libmariadb-dev pkg-config build-essential curl libpq-dev
```
Older systems might also need the following:
```bash
sudo apt install -y libssl-dev libxml2-dev libxslt1-dev libxmlsec1-dev libffi-dev apt-transport-https virtualenv
```

### Install NodeJs

```bash
curl -sL https://deb.nodesource.com/setup_14.x | sudo bash -
sudo apt install -y nodejs
```

### Install yarn to build asset files
For Debian 11 (bullseye) and above:
```bash
curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --dearmor | sudo tee /usr/share/keyrings/yarnkey.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/yarnkey.gpg] https://dl.yarnpkg.com/debian stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update && sudo apt install -y yarn
```
For older Debian systems:
```bash
sudo curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update -y
sudo apt install -y yarn
```

### Checkout source code and create virtualenv
_**Note:**_ Please adjust `/opt/web/powerdns-admin` to your local web application directory

```bash
git clone https://github.com/PowerDNS-Admin/PowerDNS-Admin.git /opt/web/powerdns-admin
cd /opt/web/powerdns-admin
python3 -mvenv ./venv
```

Activate your python3 environment and install libraries:

```bash
source ./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
## Running PowerDNS-Admin

Create PowerDNS-Admin config file and make the changes necessary for your use case. Make sure to change `SECRET_KEY` to a long random string that you generated yourself ([see Flask docs](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY)), do not use the pre-defined one. E.g.:

```bash
cp /opt/web/powerdns-admin/configs/development.py /opt/web/powerdns-admin/configs/production.py
vim /opt/web/powerdns-admin/configs/production.py
export FLASK_CONF=../configs/production.py
```

Do the DB migration

```bash
export FLASK_APP=powerdnsadmin/__init__.py
flask db upgrade
```

Then generate asset files

```bash
yarn install --pure-lockfile
flask assets build
```

Now you can run PowerDNS-Admin by command

```bash
./run.py
```

This is good for testing, but for production usage, you should use gunicorn or uwsgi. See [Running PowerDNS Admin with Systemd, Gunicorn and Nginx](../web-server/Running-PowerDNS-Admin-with-Systemd-Gunicorn-and-Nginx.md) for instructions.


From here you can now follow the [Getting started guide](../configuration/Getting-started.md).
