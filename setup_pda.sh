sudo apt install python3-dev
sudo apt install -y default-libmysqlclient-dev libsasl2-dev libldap2-dev libssl-dev libxml2-dev libxslt1-dev libxmlsec1-dev libffi-dev pkg-config apt-transport-https virtualenv build-essential curl
sudo curl -sL https://deb.nodesource.com/setup_14.x | sudo bash -
sudo apt install -y nodejs
sudo curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update -y
sudo apt install -y yarn
python3 -mvenv ./venv
source ./venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
export FLASK_CONF=../configs/development.py
export FLASK_APP=powerdnsadmin/__init__.py
flask db upgrade
yarn install --pure-lockfile
flask assets build
./run.py
