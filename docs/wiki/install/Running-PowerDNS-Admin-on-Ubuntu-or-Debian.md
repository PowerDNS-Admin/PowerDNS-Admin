## Install required packages

**Install Python 3 development package**

```bash
sudo apt install python3-dev
```

**Install required packages for building python libraries from requirements.txt file**

```bash
sudo apt install -y git libmysqlclient-dev libsasl2-dev libldap2-dev libssl-dev libxml2-dev libxslt1-dev libxmlsec1-dev libffi-dev pkg-config apt-transport-https virtualenv build-essential curl
```

_**Note:**_ I am using MySQL Community server as the database backend. So `libmysqlclient-dev` is required. For MariaDB, and PostgreSQL the required package will be difference.

** Install Maria or MySQL (ONLY if not ALREADY installed)**
```bash
sudo apt install mariadb-server mariadb-client
```
Create database and user using mysql command and entering 
```bash
>create database pda;
>grant all privileges on pda.* TO 'pda'@'localhost' identified by 'YOUR_PASSWORD_HERE';
>flush privileges;
```
**Install NodeJs**

```bash
curl -sL https://deb.nodesource.com/setup_14.x | bash -
apt install -y nodejs
```

**Install yarn to build asset files**

```bash
sudo curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update -y
sudo apt install -y yarn
```

## Checkout source code and create virtualenv
_**Note:**_ Please adjust `/opt/web/powerdns-admin` to your local web application directory

```bash
git clone https://github.com/ngoduykhanh/PowerDNS-Admin.git /opt/web/powerdns-admin
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

Open your web browser and go to `http://localhost:9191` to visit PowerDNS-Admin web interface. Register a user. The first user will be in the Administrator role.

This is good for testing, but for production usage, you should use gunicorn or uwsgi. See [Running PowerDNS Admin with Systemd, Gunicorn and Nginx](https://github.com/ngoduykhanh/PowerDNS-Admin/wiki/Running-PowerDNS-Admin-with-Systemd,-Gunicorn--and--Nginx) for instructions.